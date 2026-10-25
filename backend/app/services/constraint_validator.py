"""Deterministic hard-constraint validator."""
from __future__ import annotations
from datetime import datetime
from typing import List, Optional

from app.models.project import (
    Constraint, ConstraintCheckResult, ConstraintType, Project,
    ResolutionProposal, TaskStatus, ValidationResult, ProposedAction,
)


class ConstraintValidator:

    def validate_proposal(self, proposal: ResolutionProposal, project: Project) -> List[ConstraintCheckResult]:
        results: List[ConstraintCheckResult] = []

        # 1. Stale revision check
        results.append(self._check_revision(proposal, project))

        # 2. Per-action checks
        for action in proposal.proposed_actions:
            results.extend(self._check_action(action, project))

        # 3. Hard constraint pass: check all project constraints
        results.extend(self._check_project_constraints(proposal, project))

        return results

    # ── revision ───────────────────────────────────────────────────────────────

    def _check_revision(self, proposal: ResolutionProposal, project: Project) -> ConstraintCheckResult:
        if proposal.project_revision == project.revision:
            return ConstraintCheckResult(
                constraint_id="sys-revision",
                constraint_type=ConstraintType.HARD,
                rule="Proposal must be based on the current project revision",
                result=ValidationResult.PASS,
                evidence=f"Proposal revision {proposal.project_revision} matches current {project.revision}",
                is_hard_constraint=True,
            )
        else:
            return ConstraintCheckResult(
                constraint_id="sys-revision",
                constraint_type=ConstraintType.HARD,
                rule="Proposal must be based on the current project revision",
                result=ValidationResult.FAIL,
                evidence=(
                    f"Proposal was generated against revision {proposal.project_revision}, "
                    f"but project is now at revision {project.revision}. "
                    "Project state has changed. Regenerate proposals before executing."
                ),
                is_hard_constraint=True,
            )

    # ── per-action checks ─────────────────────────────────────────────────────

    ALLOWED_ACTION_TYPES = {
        "record_decision",
        "approve_provisional_scope",
        "modify_dependency",
        "reassign_task",
        "change_deadline",
        "record_completion_evidence",
        "update_task_status",
        "update_task_attribute",
    }

    def _check_action(self, action: ProposedAction, project: Project) -> List[ConstraintCheckResult]:
        results = []

        # Allowlist check
        if action.action_type not in self.ALLOWED_ACTION_TYPES:
            results.append(ConstraintCheckResult(
                constraint_id="sys-allowlist",
                constraint_type=ConstraintType.HARD,
                rule="Only allowlisted action types may be executed",
                result=ValidationResult.FAIL,
                evidence=f"Action type '{action.action_type}' is not in the allowlisted set. "
                         f"Allowed: {sorted(self.ALLOWED_ACTION_TYPES)}",
                is_hard_constraint=True,
            ))
            return results

        results.append(ConstraintCheckResult(
            constraint_id="sys-allowlist",
            constraint_type=ConstraintType.HARD,
            rule="Only allowlisted action types may be executed",
            result=ValidationResult.PASS,
            evidence=f"Action type '{action.action_type}' is permitted",
            is_hard_constraint=True,
        ))

        # Action-specific checks
        if action.action_type == "modify_dependency":
            results.extend(self._check_modify_dependency(action, project))

        elif action.action_type == "approve_provisional_scope":
            results.extend(self._check_approve_provisional(action, project))

        elif action.action_type == "reassign_task":
            results.extend(self._check_reassign_task(action, project))

        elif action.action_type == "update_task_status":
            results.extend(self._check_update_status(action, project))

        elif action.action_type == "change_deadline":
            results.extend(self._check_change_deadline(action, project))

        return results

    def _check_modify_dependency(self, action: ProposedAction, project: Project) -> List[ConstraintCheckResult]:
        results = []
        task_id = action.target_task_id
        dep_to_remove = action.parameters.get("remove_dependency")

        task = project.get_task(task_id or "")
        if not task:
            results.append(ConstraintCheckResult(
                constraint_id="dep-target-exists",
                constraint_type=ConstraintType.HARD,
                rule="Target task must exist",
                result=ValidationResult.FAIL,
                evidence=f"Task '{task_id}' not found in project",
                is_hard_constraint=True,
            ))
            return results

        if not task.dependencies_mutable:
            results.append(ConstraintCheckResult(
                constraint_id="dep-mutable",
                constraint_type=ConstraintType.HARD,
                rule="Task dependencies must be mutable to modify them",
                result=ValidationResult.FAIL,
                evidence=f"Task '{task.title}' has dependencies_mutable=false. "
                         f"Its dependencies are protected and cannot be changed.",
                is_hard_constraint=True,
            ))
            return results

        # Check if removing a protected dependency
        for constraint in project.constraints:
            if constraint.constraint_type == ConstraintType.PROTECTED_DEPENDENCY and constraint.is_active:
                protected_dep = (constraint.value or {}).get("protected_dep")
                if (
                    constraint.applies_to and task_id in constraint.applies_to
                    and dep_to_remove == protected_dep
                ):
                    results.append(ConstraintCheckResult(
                        constraint_id=constraint.constraint_id,
                        constraint_type=ConstraintType.PROTECTED_DEPENDENCY,
                        rule="Protected dependencies cannot be removed",
                        result=ValidationResult.FAIL,
                        evidence=(
                            f"Constraint '{constraint.description}' protects dependency "
                            f"'{protected_dep}' on task '{task.title}'. "
                            f"Removing this dependency is not permitted."
                        ),
                        is_hard_constraint=True,
                    ))
                    return results

        results.append(ConstraintCheckResult(
            constraint_id="dep-allowed",
            constraint_type=ConstraintType.HARD,
            rule="Dependency modification is permitted",
            result=ValidationResult.PASS,
            evidence=f"Task '{task.title}' has mutable dependencies and no protected constraint blocks this change",
            is_hard_constraint=False,
        ))
        return results

    def _check_approve_provisional(self, action: ProposedAction, project: Project) -> List[ConstraintCheckResult]:
        results = []
        acting_member_id = action.parameters.get("acting_member_id")

        # Check permission constraint
        for constraint in project.constraints:
            if constraint.constraint_type == ConstraintType.PERMISSION and constraint.is_active:
                allowed = (constraint.value or {}).get("allowed_approvers", [])
                if allowed:
                    if acting_member_id not in allowed:
                        results.append(ConstraintCheckResult(
                            constraint_id=constraint.constraint_id,
                            constraint_type=ConstraintType.PERMISSION,
                            rule="Only authorized team members can approve provisional scope",
                            result=ValidationResult.FAIL,
                            evidence=(
                                f"Member '{acting_member_id}' is not in the list of authorized approvers: "
                                f"{allowed}. Constraint: '{constraint.description}'"
                            ),
                            is_hard_constraint=True,
                        ))
                        return results
                    else:
                        results.append(ConstraintCheckResult(
                            constraint_id=constraint.constraint_id,
                            constraint_type=ConstraintType.PERMISSION,
                            rule="Only authorized team members can approve provisional scope",
                            result=ValidationResult.PASS,
                            evidence=f"Member '{acting_member_id}' is an authorized approver",
                            is_hard_constraint=True,
                        ))

        if not results:
            results.append(ConstraintCheckResult(
                constraint_id="perm-default",
                constraint_type=ConstraintType.PERMISSION,
                rule="Only authorized team members can approve provisional scope",
                result=ValidationResult.NEEDS_INFORMATION,
                evidence="No acting_member_id provided. Cannot verify authorization.",
                is_hard_constraint=True,
            ))
        return results

    def _check_reassign_task(self, action: ProposedAction, project: Project) -> List[ConstraintCheckResult]:
        results = []
        task_id = action.target_task_id
        new_member_id = action.parameters.get("new_member_id")

        task = project.get_task(task_id or "")
        member = project.get_member(new_member_id or "")

        if not task:
            results.append(ConstraintCheckResult(
                constraint_id="reassign-task-exists",
                constraint_type=ConstraintType.HARD,
                rule="Task must exist",
                result=ValidationResult.FAIL,
                evidence=f"Task '{task_id}' not found",
                is_hard_constraint=True,
            ))
            return results

        if not member:
            results.append(ConstraintCheckResult(
                constraint_id="reassign-member-exists",
                constraint_type=ConstraintType.HARD,
                rule="Target member must exist in the project",
                result=ValidationResult.FAIL,
                evidence=f"Member '{new_member_id}' not found in project",
                is_hard_constraint=True,
            ))
            return results

        # Skill check
        missing_skills = [s for s in task.required_skills if s not in member.skills]
        if missing_skills:
            results.append(ConstraintCheckResult(
                constraint_id="reassign-skills",
                constraint_type=ConstraintType.HARD,
                rule="Assignee must have required skills",
                result=ValidationResult.FAIL,
                evidence=(
                    f"Member '{member.name}' lacks required skills for '{task.title}': "
                    f"{missing_skills}. Member skills: {member.skills}"
                ),
                is_hard_constraint=True,
            ))
            return results

        results.append(ConstraintCheckResult(
            constraint_id="reassign-ok",
            constraint_type=ConstraintType.HARD,
            rule="Reassignment is valid",
            result=ValidationResult.PASS,
            evidence=f"Member '{member.name}' has all required skills and exists in project",
            is_hard_constraint=False,
        ))
        return results

    def _check_update_status(self, action: ProposedAction, project: Project) -> List[ConstraintCheckResult]:
        results = []
        task_id = action.target_task_id
        new_status = action.parameters.get("new_status")
        task = project.get_task(task_id or "")

        if not task:
            results.append(ConstraintCheckResult(
                constraint_id="status-task-exists",
                constraint_type=ConstraintType.HARD,
                rule="Task must exist",
                result=ValidationResult.FAIL,
                evidence=f"Task '{task_id}' not found",
                is_hard_constraint=True,
            ))
            return results

        # Do not allow marking a task COMPLETED without evidence if evidence required
        if new_status == "COMPLETED":
            for constraint in project.constraints:
                if (
                    constraint.constraint_type == ConstraintType.EVIDENCE_REQUIRED
                    and constraint.is_active
                    and constraint.applies_to
                    and task_id in constraint.applies_to
                ):
                    if not task.completion_evidence and not action.parameters.get("evidence"):
                        results.append(ConstraintCheckResult(
                            constraint_id=constraint.constraint_id,
                            constraint_type=ConstraintType.EVIDENCE_REQUIRED,
                            rule="Completion evidence required before marking task as COMPLETED",
                            result=ValidationResult.FAIL,
                            evidence=(
                                f"Task '{task.title}' requires completion evidence "
                                f"({(constraint.value or {}).get('evidence_type', 'evidence')}) "
                                f"but none was provided."
                            ),
                            is_hard_constraint=True,
                        ))
                        return results

        # Do not allow bypassing mandatory security review
        for constraint in project.constraints:
            if constraint.constraint_type == ConstraintType.MANDATORY_REVIEW and constraint.is_active:
                if (constraint.applies_to and task_id in constraint.applies_to and
                        new_status == "COMPLETED" and task.is_protected and not task.completion_evidence):
                    results.append(ConstraintCheckResult(
                        constraint_id=constraint.constraint_id,
                        constraint_type=ConstraintType.MANDATORY_REVIEW,
                        rule="Mandatory review tasks cannot be marked complete without evidence",
                        result=ValidationResult.FAIL,
                        evidence=f"'{task.title}' is a mandatory review (protected). "
                                 f"Cannot mark complete without proper evidence.",
                        is_hard_constraint=True,
                    ))
                    return results

        results.append(ConstraintCheckResult(
            constraint_id="status-ok",
            constraint_type=ConstraintType.HARD,
            rule="Status update is valid",
            result=ValidationResult.PASS,
            evidence=f"Status change for '{task.title}' to {new_status} passes all checks",
            is_hard_constraint=False,
        ))
        return results

    def _check_change_deadline(self, action: ProposedAction, project: Project) -> List[ConstraintCheckResult]:
        results = []
        new_deadline_str = action.parameters.get("new_deadline")
        acting_member_id = action.parameters.get("acting_member_id")

        # Check permission
        member = project.get_member(acting_member_id or "")
        if not member or "modify_deadline" not in member.permissions:
            results.append(ConstraintCheckResult(
                constraint_id="deadline-permission",
                constraint_type=ConstraintType.PERMISSION,
                rule="Only authorized members can change deadlines",
                result=ValidationResult.FAIL,
                evidence=f"Member '{acting_member_id}' does not have 'modify_deadline' permission",
                is_hard_constraint=True,
            ))
            return results

        # Check the new deadline does not exceed project hard deadline
        if new_deadline_str:
            try:
                new_deadline = datetime.fromisoformat(new_deadline_str)
                if new_deadline > project.deadline:
                    results.append(ConstraintCheckResult(
                        constraint_id="deadline-hard-limit",
                        constraint_type=ConstraintType.DEADLINE,
                        rule="Task deadlines cannot exceed project hard deadline",
                        result=ValidationResult.FAIL,
                        evidence=(
                            f"New deadline {new_deadline.date()} exceeds project deadline "
                            f"{project.deadline.date()}."
                        ),
                        is_hard_constraint=True,
                    ))
                    return results
            except ValueError:
                results.append(ConstraintCheckResult(
                    constraint_id="deadline-format",
                    constraint_type=ConstraintType.DEADLINE,
                    rule="Deadline must be a valid ISO datetime",
                    result=ValidationResult.FAIL,
                    evidence=f"Could not parse '{new_deadline_str}' as ISO datetime",
                    is_hard_constraint=True,
                ))
                return results

        results.append(ConstraintCheckResult(
            constraint_id="deadline-ok",
            constraint_type=ConstraintType.DEADLINE,
            rule="Deadline change is valid",
            result=ValidationResult.PASS,
            evidence=f"Member '{member.name}' is authorized and deadline is within project bounds",
            is_hard_constraint=False,
        ))
        return results

    def _check_project_constraints(self, proposal: ResolutionProposal, project: Project) -> List[ConstraintCheckResult]:
        """Run all project-level constraint checks."""
        results = []
        for constraint in project.constraints:
            if not constraint.is_active:
                continue
            if constraint.constraint_type == ConstraintType.MANDATORY_REVIEW:
                # Any proposal that claims to bypass mandatory review fails
                for action in proposal.proposed_actions:
                    if action.action_type == "remove_mandatory_review":
                        results.append(ConstraintCheckResult(
                            constraint_id=constraint.constraint_id,
                            constraint_type=ConstraintType.MANDATORY_REVIEW,
                            rule="Mandatory review tasks cannot be removed or bypassed",
                            result=ValidationResult.FAIL,
                            evidence=f"Constraint: {constraint.description}",
                            is_hard_constraint=True,
                        ))
        return results

    def is_feasible(self, checks: List[ConstraintCheckResult]) -> bool:
        """A proposal is feasible if no HARD constraint check returned FAIL."""
        for check in checks:
            if check.is_hard_constraint and check.result == ValidationResult.FAIL:
                return False
        return True

    def infeasibility_reason(self, checks: List[ConstraintCheckResult]) -> Optional[str]:
        reasons = []
        for check in checks:
            if check.is_hard_constraint and check.result == ValidationResult.FAIL:
                reasons.append(f"[{check.constraint_type.value}] {check.rule}: {check.evidence}")
        return " | ".join(reasons) if reasons else None

    def score_proposal(self, proposal: ResolutionProposal, project: Project) -> tuple[float, str]:
        """
        Transparent scoring. Only call for feasible proposals.
        Returns (score 0-100, explanation).
        """
        score = 50.0
        factors = []

        # + tasks unblocked
        n_unblocked = len(proposal.affected_task_ids)
        score += min(n_unblocked * 5, 20)
        factors.append(f"+{min(n_unblocked * 5, 20):.0f} for unblocking {n_unblocked} task(s)")

        # - effort cost
        effort_penalty = min(proposal.estimated_effort_hours / 10, 10)
        score -= effort_penalty
        factors.append(f"-{effort_penalty:.1f} for {proposal.estimated_effort_hours:.0f}h effort cost")

        # - deadline impact
        if proposal.deadline_impact_days > 0:
            penalty = min(proposal.deadline_impact_days * 2, 20)
            score -= penalty
            factors.append(f"-{penalty:.0f} for {proposal.deadline_impact_days}d deadline impact")

        # - risks
        n_risks = len(proposal.risks)
        risk_penalty = min(n_risks * 3, 15)
        score -= risk_penalty
        factors.append(f"-{risk_penalty:.0f} for {n_risks} identified risk(s)")

        # + assumptions clearly stated (reversibility proxy)
        if proposal.assumptions:
            score += 5
            factors.append("+5 for explicitly documented assumptions")

        score = max(0.0, min(100.0, score))
        explanation = "Score: " + ", ".join(factors) + f" → Total: {score:.0f}/100"
        return score, explanation
