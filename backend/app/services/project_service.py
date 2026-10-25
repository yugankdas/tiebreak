"""Central project service — manages project state and orchestrates services."""
from __future__ import annotations
import copy
import json
from pathlib import Path
from typing import Dict, List, Optional
import uuid

from app.models.project import (
    AuditAction, Blocker, Project, ResolutionProposal, TaskStatus,
    ApprovalState, ExecutionState, VerificationState, ExecutionResult, VerificationResult,
)
from app.services.graph_engine import GraphEngine, GraphAnalysis, get_graph_engine
from app.services.deadlock_detector import DeadlockDetector
from app.services.constraint_validator import ConstraintValidator
from app.services.resolution_generator import ResolutionGenerator
from app.services.action_executor import ActionExecutor
from app.services.outcome_verifier import OutcomeVerifier
from app.services.audit_service import AuditService
from app.services.failproof_adapter import FailproofAdapter
from app.services.approval_service import ApprovalRoutingService


DEMO_PROJECT_PATH = Path(__file__).parent.parent / "data" / "demo_project.json"


class ProjectService:
    def __init__(
        self,
        engine: GraphEngine,
        detector: DeadlockDetector,
        validator: ConstraintValidator,
        generator: ResolutionGenerator,
        executor: ActionExecutor,
        verifier: OutcomeVerifier,
        audit: AuditService,
        failproof: FailproofAdapter,
        approvals: Optional[ApprovalRoutingService] = None,
    ):
        self.engine = engine
        self.detector = detector
        self.validator = validator
        self.generator = generator
        self.executor = executor
        self.verifier = verifier
        self.audit = audit
        self.failproof = failproof
        self.approvals = approvals or ApprovalRoutingService()

        self._projects: Dict[str, Project] = {}
        self._original_demo: Optional[dict] = None  # for reset
        self._blockers: Dict[str, List[Blocker]] = {}  # project_id -> blockers
        self._resolutions: Dict[str, ResolutionProposal] = {}  # resolution_id -> proposal
        self._execution_results: Dict[str, ExecutionResult] = {}
        self._verification_results: Dict[str, VerificationResult] = {}

        self._load_demo()

    def _load_demo(self) -> None:
        try:
            raw = json.loads(DEMO_PROJECT_PATH.read_text())
            self._original_demo = raw
            project = Project(**raw)
            self._projects[project.project_id] = project
        except Exception as e:
            print(f"[ProjectService] Failed to load demo project: {e}")

    # ── project access ─────────────────────────────────────────────────────────

    def list_projects(self) -> List[Project]:
        return list(self._projects.values())

    def get_project(self, project_id: str) -> Optional[Project]:
        return self._projects.get(project_id)

    def reset_demo(self, project_id: str) -> Optional[Project]:
        if not self._original_demo:
            return None
        raw = copy.deepcopy(self._original_demo)
        project = Project(**raw)
        self._projects[project_id] = project
        # Clear associated state
        self._blockers.pop(project_id, None)
        related_resolutions = [
            rid for rid, r in self._resolutions.items()
            if r.project_id == project_id
        ]
        for rid in related_resolutions:
            self._resolutions.pop(rid, None)
            self._execution_results.pop(rid, None)
            self._verification_results.pop(rid, None)
        self.audit.record(
            action=AuditAction.PROJECT_RESET,
            target=f"project:{project_id}",
            input_summary="Project reset to initial demo state",
            outcome="Project restored to revision 0",
            resulting_revision=0,
        )
        return project

    # ── graph ──────────────────────────────────────────────────────────────────

    def get_graph(self, project_id: str) -> Optional[dict]:
        project = self.get_project(project_id)
        if not project:
            return None
        analysis = self.engine.analyse(project)
        return analysis.graph_data

    # ── blocker detection ──────────────────────────────────────────────────────

    def detect_blockers(self, project_id: str) -> List[Blocker]:
        project = self.get_project(project_id)
        if not project:
            return []

        blockers = self.detector.detect_all(project)
        self._blockers[project_id] = blockers

        self.failproof.record_blocker_detection(
            len(blockers),
            [b.blocker_type.value for b in blockers],
        )
        self.audit.record(
            action=AuditAction.BLOCKER_DETECTED,
            target=f"project:{project_id}",
            input_summary=f"Ran blocker detection on project '{project.name}'",
            outcome=f"Found {len(blockers)} blocker(s): {[b.title for b in blockers]}",
        )
        return blockers

    def get_blockers(self, project_id: str) -> List[Blocker]:
        if project_id not in self._blockers:
            return self.detect_blockers(project_id)
        return self._blockers.get(project_id, [])

    def get_blocker(self, project_id: str, blocker_id: str) -> Optional[Blocker]:
        for b in self.get_blockers(project_id):
            if b.blocker_id == blocker_id:
                return b
        return None

    # ── resolution generation & routing ────────────────────────────────────────

    def generate_resolutions(self, project_id: str, blocker_id: str) -> List[ResolutionProposal]:
        project = self.get_project(project_id)
        blocker = self.get_blocker(project_id, blocker_id)
        if not project or not blocker:
            return []

        proposals = self.generator.generate(blocker, project)

        # Validate each proposal and create routed approval requests
        for p in proposals:
            checks = self.validator.validate_proposal(p, project)
            p.constraint_checks = checks
            feasible = self.validator.is_feasible(checks)
            p.is_feasible = feasible
            if not feasible:
                p.infeasibility_reason = self.validator.infeasibility_reason(checks)
            else:
                score, explanation = self.validator.score_proposal(p, project)
                p.score = score
                p.score_explanation = explanation

            # Route proposal through Organization Approval Routing Service
            if self.approvals:
                req = self.approvals.route_proposal(p, project, requester_id="mem-01")
                p.approval_request_id = req.request_id
                p.designated_approver_ids = req.designated_approver_ids
                p.routing_reason = req.routing_reason

            self._resolutions[p.resolution_id] = p

        self.failproof.record_resolution_generated(
            blocker_id, len(proposals), proposals[0].is_fallback if proposals else True
        )
        self.audit.record(
            action=AuditAction.RESOLUTION_GENERATED,
            target=f"project:{project_id}/blocker:{blocker_id}",
            input_summary=f"Generated resolutions for blocker '{blocker.title}'",
            outcome=(
                f"Generated {len(proposals)} proposals. "
                f"Feasible: {sum(1 for p in proposals if p.is_feasible)}. "
                f"{'Using deterministic fallback' if proposals and proposals[0].is_fallback else 'Using Groq LLM'}"
            ),
        )
        return proposals

    def get_resolution(self, resolution_id: str) -> Optional[ResolutionProposal]:
        return self._resolutions.get(resolution_id)

    def get_resolutions_for_project(self, project_id: str) -> List[ResolutionProposal]:
        return [r for r in self._resolutions.values() if r.project_id == project_id]

    # ── validation ────────────────────────────────────────────────────────────

    def validate_resolution(self, project_id: str, resolution_id: str) -> Optional[ResolutionProposal]:
        project = self.get_project(project_id)
        proposal = self.get_resolution(resolution_id)
        if not project or not proposal:
            return None

        checks = self.validator.validate_proposal(proposal, project)
        proposal.constraint_checks = checks
        feasible = self.validator.is_feasible(checks)
        proposal.is_feasible = feasible
        proposal.infeasibility_reason = self.validator.infeasibility_reason(checks) if not feasible else None
        if feasible:
            score, explanation = self.validator.score_proposal(proposal, project)
            proposal.score = score
            proposal.score_explanation = explanation

        self.failproof.record_constraint_validation(resolution_id, feasible)
        self.audit.record(
            action=AuditAction.RESOLUTION_VALIDATED,
            target=f"resolution:{resolution_id}",
            input_summary=f"Validated resolution '{proposal.title}'",
            outcome=f"{'FEASIBLE' if feasible else 'INFEASIBLE'}: {proposal.infeasibility_reason or 'All constraints passed'}",
            validation_results=checks,
        )
        return proposal

    # ── approval ──────────────────────────────────────────────────────────────

    def approve_resolution(self, project_id: str, resolution_id: str, actor: str = "user") -> Optional[ResolutionProposal]:
        project = self.get_project(project_id)
        proposal = self.get_resolution(resolution_id)
        if not project or not proposal:
            return None
        if not proposal.is_feasible:
            raise ValueError("Cannot approve an infeasible proposal")
        if proposal.approval_state == ApprovalState.APPROVED:
            return proposal  # already approved

        proposal.approval_state = ApprovalState.APPROVED
        from datetime import datetime
        proposal.approved_at = datetime.utcnow()

        self.failproof.record_approval(resolution_id, True)
        self.audit.record(
            action=AuditAction.RESOLUTION_APPROVED,
            target=f"resolution:{resolution_id}",
            input_summary=f"User approved resolution '{proposal.title}'",
            outcome="Resolution approved and ready for execution",
            actor=actor,
        )
        return proposal

    def reject_resolution(self, project_id: str, resolution_id: str, actor: str = "user", reason: str = "") -> Optional[ResolutionProposal]:
        proposal = self.get_resolution(resolution_id)
        if not proposal:
            return None
        proposal.approval_state = ApprovalState.REJECTED

        self.failproof.record_approval(resolution_id, False)
        self.audit.record(
            action=AuditAction.RESOLUTION_REJECTED,
            target=f"resolution:{resolution_id}",
            input_summary=f"User rejected resolution '{proposal.title}'. Reason: {reason}",
            outcome="Resolution rejected",
            actor=actor,
        )
        return proposal

    # ── execution ─────────────────────────────────────────────────────────────

    def execute_resolution(self, project_id: str, resolution_id: str) -> Optional[ExecutionResult]:
        project = self.get_project(project_id)
        proposal = self.get_resolution(resolution_id)
        if not project or not proposal:
            return None

        prev_revision = project.revision

        # Backend enforcement: require approval
        if proposal.approval_state != ApprovalState.APPROVED:
            result = ExecutionResult(
                success=False,
                error="Backend enforcement: proposal must be APPROVED before execution",
            )
            self._execution_results[resolution_id] = result
            return result

        # Backend enforcement: require feasibility
        if not proposal.is_feasible:
            result = ExecutionResult(
                success=False,
                error="Backend enforcement: infeasible proposals cannot be executed",
            )
            self._execution_results[resolution_id] = result
            return result

        # Stale state check: proposal revision must match project revision
        if proposal.project_revision != project.revision:
            result = ExecutionResult(
                success=False,
                error=f"Stale proposal: Proposal was synthesized on revision {proposal.project_revision}, but project is now at revision {project.revision}. Re-synthesis required.",
            )
            self._execution_results[resolution_id] = result
            return result

        proposal.execution_state = ExecutionState.EXECUTING
        result = self.executor.execute(proposal, project)

        if result.success:
            proposal.execution_state = ExecutionState.EXECUTED
            from datetime import datetime
            proposal.executed_at = datetime.utcnow()
            
            # Recompute blockers immediately so authoritative state is updated
            self.detect_blockers(project_id)
        else:
            proposal.execution_state = ExecutionState.FAILED

        self._execution_results[resolution_id] = result

        self.failproof.record_execution(resolution_id, result.success, result.state_changes)
        self.audit.record(
            action=AuditAction.ACTION_EXECUTED,
            target=f"resolution:{resolution_id}",
            input_summary=f"Executed resolution '{proposal.title}'",
            outcome=f"{'Success' if result.success else 'Failed'}: {result.state_changes}",
            error_details=result.error,
            previous_revision=prev_revision,
            resulting_revision=project.revision,
        )
        if result.state_changes:
            self.audit.record(
                action=AuditAction.STATE_CHANGED,
                target=f"project:{project_id}",
                input_summary=f"State mutation from resolution '{proposal.title}'",
                outcome="; ".join(result.state_changes),
                previous_revision=prev_revision,
                resulting_revision=project.revision,
            )
        return result

    def get_execution_result(self, resolution_id: str) -> Optional[ExecutionResult]:
        return self._execution_results.get(resolution_id)

    # ── verification ──────────────────────────────────────────────────────────

    def verify_resolution(self, project_id: str, resolution_id: str, blocker_id: str) -> Optional[VerificationResult]:
        project = self.get_project(project_id)
        proposal = self.get_resolution(resolution_id)
        # Snapshot the blocker BEFORE re-detection (cycle removal can delete the blocker)
        blocker = self.get_blocker(project_id, blocker_id)
        if not project or not proposal:
            return None

        # If the blocker has already been resolved/removed, synthesize a VERIFIED_RESOLVED result
        if not blocker:
            from app.models.project import VerificationState as VS, BlockerStatus
            tasks_ready = [t.task_id for t in project.tasks if t.task_id in self.engine.analyse(project).tasks_ready]
            tasks_blocked = [t.task_id for t in project.tasks if t.status.value == 'BLOCKED']
            result = VerificationResult(
                verification_state=VS.VERIFIED_RESOLVED,
                original_blocker_resolved=True,
                tasks_now_ready=tasks_ready,
                tasks_still_blocked=tasks_blocked,
                new_blockers=[],
                evidence=[f"Blocker {blocker_id} no longer present in project state — original constraint resolved by execution."],
            )
            proposal.verification_state = result.verification_state
            self._verification_results[resolution_id] = result
            self.failproof.record_verification(resolution_id, result.verification_state.value)
            return result

        result = self.verifier.verify(proposal, blocker, project)
        proposal.verification_state = result.verification_state
        self._verification_results[resolution_id] = result

        # Update blocker status
        if result.original_blocker_resolved:
            from app.models.project import BlockerStatus
            blocker.status = BlockerStatus.RESOLVED if result.verification_state == VerificationState.VERIFIED_RESOLVED else BlockerStatus.PARTIALLY_RESOLVED

        # Re-detect all blockers so authoritative project state reflects newly resolved/unblocked tasks
        self.detect_blockers(project_id)

        self.failproof.record_verification(resolution_id, result.verification_state.value)
        self.audit.record(
            action=AuditAction.VERIFICATION_COMPLETED,
            target=f"resolution:{resolution_id}",
            input_summary=f"Verified outcome of resolution '{proposal.title}'",
            outcome=f"{result.verification_state.value}: {result.evidence}",
        )
        return result

    def get_verification_result(self, resolution_id: str) -> Optional[VerificationResult]:
        return self._verification_results.get(resolution_id)
