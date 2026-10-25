"""Independent outcome verifier — verifies actual project state after execution."""
from __future__ import annotations
from datetime import datetime
from typing import List

from app.models.project import (
    Blocker, BlockerType, Project, ResolutionProposal,
    TaskStatus, VerificationResult, VerificationState,
)
from app.services.deadlock_detector import DeadlockDetector
from app.services.graph_engine import GraphEngine


class OutcomeVerifier:
    def __init__(self, engine: GraphEngine, detector: DeadlockDetector):
        self.engine = engine
        self.detector = detector

    def verify(
        self,
        proposal: ResolutionProposal,
        original_blocker: Blocker,
        project: Project,
    ) -> VerificationResult:
        """
        Independently verify whether the intervention resolved the original blocker.
        Does NOT trust the executor's success message. Re-reads actual project state.
        """
        analysis = self.engine.analyse(project)
        current_blockers = self.detector.detect_all(project)

        # Was the original blocker resolved?
        original_resolved = self._check_original_blocker_resolved(
            original_blocker, analysis, current_blockers
        )

        # Which tasks are now ready?
        tasks_now_ready = [
            t.task_id for t in project.tasks
            if t.task_id in analysis.tasks_ready
        ]

        # Which tasks remain blocked?
        tasks_still_blocked = [
            t.task_id for t in project.tasks
            if t.status == TaskStatus.BLOCKED
        ]

        # New blockers introduced?
        new_blocker_ids = [b.blocker_id for b in current_blockers]
        new_blockers = [
            b.blocker_id for b in current_blockers
            if b.blocker_id != original_blocker.blocker_id
        ]

        # Build evidence
        evidence = []
        evidence.append(f"Graph recomputed after execution (project revision {project.revision})")
        evidence.append(f"Tasks now ready: {tasks_now_ready}")
        evidence.append(f"Tasks still blocked: {tasks_still_blocked}")
        evidence.append(f"Active cycles after execution: {analysis.cycles}")
        evidence.append(f"Current blockers: {[b.title for b in current_blockers]}")

        # Determine verification state
        if not original_resolved and not new_blockers:
            state = VerificationState.NOT_RESOLVED
        elif original_resolved and not new_blockers:
            # Check if all affected tasks are now unblocked
            affected_still_blocked = [
                tid for tid in proposal.affected_task_ids
                if tid in tasks_still_blocked
            ]
            if affected_still_blocked:
                state = VerificationState.PARTIALLY_RESOLVED
                evidence.append(
                    f"Original blocker addressed but some affected tasks still blocked: "
                    f"{affected_still_blocked}"
                )
            else:
                state = VerificationState.VERIFIED_RESOLVED
        elif original_resolved and new_blockers:
            state = VerificationState.NEW_BLOCKER_DETECTED
            evidence.append(
                f"WARNING: Original blocker resolved but new blockers detected: "
                f"{[b.title for b in current_blockers if b.blocker_id in new_blockers]}"
            )
        else:
            state = VerificationState.NOT_RESOLVED

        return VerificationResult(
            verification_state=state,
            original_blocker_resolved=original_resolved,
            tasks_now_ready=tasks_now_ready,
            tasks_still_blocked=tasks_still_blocked,
            new_blockers=new_blockers,
            evidence=evidence,
            verified_at=datetime.utcnow(),
        )

    def _check_original_blocker_resolved(
        self,
        blocker: Blocker,
        analysis,
        current_blockers: List[Blocker],
    ) -> bool:
        if blocker.blocker_type == BlockerType.CIRCULAR_DEPENDENCY:
            # Check if the specific cycle is gone
            if not analysis.cycles:
                return True
            # Check if the original cycle's tasks are no longer all in cycles
            if blocker.cycle_nodes:
                cycle_set = set(blocker.cycle_nodes)
                for current_cycle in analysis.cycles:
                    if cycle_set.issubset(set(current_cycle)):
                        return False  # same cycle still present
                return True
            return len(analysis.cycles) == 0

        elif blocker.blocker_type == BlockerType.MISSING_DECISION:
            # Check if the decision task is resolved
            for b in current_blockers:
                if (b.blocker_type == BlockerType.MISSING_DECISION
                        and set(b.affected_task_ids) == set(blocker.affected_task_ids)):
                    return False
            return True

        elif blocker.blocker_type == BlockerType.RESOURCE_CONFLICT:
            for b in current_blockers:
                if (b.blocker_type == BlockerType.RESOURCE_CONFLICT
                        and b.affected_task_ids == blocker.affected_task_ids):
                    return False
            return True

        else:
            # Generic: blocker no longer in current list
            return not any(
                b.blocker_id == blocker.blocker_id for b in current_blockers
            )
