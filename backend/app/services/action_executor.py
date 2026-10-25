"""Allowlisted action executor — mutates project state safely."""
from __future__ import annotations
from datetime import datetime
from typing import Any, Dict, List, Optional

from app.models.project import (
    ExecutionResult, ProposedAction, Project, ResolutionProposal,
    TaskStatus, AuditEvent, AuditAction, ConstraintCheckResult, ValidationResult,
)
from app.services.constraint_validator import ConstraintValidator


class ActionExecutor:
    """
    Executes only allowlisted actions against the project state.
    Never executes arbitrary code or LLM-generated strings.
    """

    def __init__(self, validator: ConstraintValidator):
        self.validator = validator

    def execute(
        self,
        proposal: ResolutionProposal,
        project: Project,
    ) -> ExecutionResult:
        result = ExecutionResult(success=False)

        # Pre-execution checks
        if proposal.approval_state.value != "APPROVED":
            result.error = "Proposal must be APPROVED before execution"
            return result

        if proposal.execution_state.value == "EXECUTED":
            # Idempotent: already executed
            result.success = True
            result.state_changes.append("Already executed — no action taken")
            return result

        # Revalidate constraints
        checks = self.validator.validate_proposal(proposal, project)
        if not self.validator.is_feasible(checks):
            result.error = (
                "Pre-execution revalidation failed: "
                + (self.validator.infeasibility_reason(checks) or "unknown")
            )
            return result

        # Execute each action
        for action in proposal.proposed_actions:
            action_result: Dict[str, Any] = {
                "action_type": action.action_type,
                "description": action.description,
            }
            result.actions_attempted.append(action_result)
            try:
                changes = self._dispatch(action, project)
                action_result["success"] = True
                action_result["changes"] = changes
                result.actions_succeeded.append(action_result)
                result.state_changes.extend(changes)
            except Exception as e:
                action_result["success"] = False
                action_result["error"] = str(e)
                result.actions_failed.append(action_result)
                result.error = f"Action '{action.action_type}' failed: {e}"
                result.success = False
                return result

        # Increment project revision
        project.revision += 1
        project.updated_at = datetime.utcnow()
        self._recompute_statuses(project)

        result.success = True
        result.executed_at = datetime.utcnow()
        return result

    def _dispatch(self, action: ProposedAction, project: Project) -> List[str]:
        dispatch_map = {
            "record_decision": self._record_decision,
            "approve_provisional_scope": self._approve_provisional_scope,
            "modify_dependency": self._modify_dependency,
            "reassign_task": self._reassign_task,
            "change_deadline": self._change_deadline,
            "record_completion_evidence": self._record_completion_evidence,
            "update_task_status": self._update_task_status,
            "update_task_attribute": self._update_task_attribute,
        }
        handler = dispatch_map.get(action.action_type)
        if not handler:
            raise ValueError(f"Action type '{action.action_type}' is not in the allowlist")
        return handler(action, project)

    def _record_decision(self, action: ProposedAction, project: Project) -> List[str]:
        task = project.get_task(action.target_task_id or "")
        decision = action.parameters.get("decision", "Decision recorded")
        if task:
            task.blocker_reason = None
            task.completion_evidence = decision
            task.state_revision += 1
            return [f"Recorded decision on task '{task.title}': {decision}"]
        return [f"Recorded global decision: {decision}"]

    def _approve_provisional_scope(self, action: ProposedAction, project: Project) -> List[str]:
        task = project.get_task(action.target_task_id or "")
        note = action.parameters.get("provisional_note", "Provisional scope approved")
        if task:
            task.completion_evidence = note
            task.tags = list(set(task.tags + ["provisional"]))
            task.blocker_reason = None
            task.state_revision += 1
            return [f"Approved provisional scope for '{task.title}': {note}"]
        return [f"Approved provisional scope globally: {note}"]

    def _modify_dependency(self, action: ProposedAction, project: Project) -> List[str]:
        task = project.get_task(action.target_task_id or "")
        if not task:
            raise ValueError(f"Task '{action.target_task_id}' not found")
        if not task.dependencies_mutable:
            raise ValueError(f"Task '{task.title}' dependencies are not mutable")

        changes = []
        remove_dep = action.parameters.get("remove_dependency")
        add_dep = action.parameters.get("add_dependency")

        if remove_dep and remove_dep in task.dependencies:
            task.dependencies.remove(remove_dep)
            task.state_revision += 1
            changes.append(f"Removed dependency '{remove_dep}' from task '{task.title}'")
        elif remove_dep:
            changes.append(f"Dependency '{remove_dep}' was not present in '{task.title}' — no change")

        if add_dep and add_dep not in task.dependencies:
            task.dependencies.append(add_dep)
            task.state_revision += 1
            changes.append(f"Added dependency '{add_dep}' to task '{task.title}'")

        return changes

    def _reassign_task(self, action: ProposedAction, project: Project) -> List[str]:
        task = project.get_task(action.target_task_id or "")
        new_member = project.get_member(action.parameters.get("new_member_id", ""))
        if not task:
            raise ValueError(f"Task '{action.target_task_id}' not found")
        if not new_member:
            raise ValueError(f"Member '{action.parameters.get('new_member_id')}' not found")

        old_owner = task.owner_id
        task.owner_id = new_member.member_id
        task.state_revision += 1

        # Update assignments
        if old_owner:
            old_member = project.get_member(old_owner)
            if old_member and task.task_id in old_member.current_assignments:
                old_member.current_assignments.remove(task.task_id)
        if task.task_id not in new_member.current_assignments:
            new_member.current_assignments.append(task.task_id)

        return [f"Reassigned '{task.title}' from '{old_owner}' to '{new_member.name}'"]

    def _change_deadline(self, action: ProposedAction, project: Project) -> List[str]:
        task = project.get_task(action.target_task_id or "")
        new_dl_str = action.parameters.get("new_deadline")
        if not task:
            raise ValueError(f"Task '{action.target_task_id}' not found")
        if not new_dl_str:
            raise ValueError("new_deadline parameter is required")
        new_dl = datetime.fromisoformat(new_dl_str)
        old_dl = task.deadline
        task.deadline = new_dl
        task.state_revision += 1
        return [f"Changed deadline for '{task.title}' from {old_dl} to {new_dl}"]

    def _record_completion_evidence(self, action: ProposedAction, project: Project) -> List[str]:
        task = project.get_task(action.target_task_id or "")
        evidence = action.parameters.get("evidence", "")
        if not task:
            raise ValueError(f"Task '{action.target_task_id}' not found")
        task.completion_evidence = evidence
        task.state_revision += 1
        return [f"Recorded completion evidence for '{task.title}': {evidence}"]

    def _update_task_status(self, action: ProposedAction, project: Project) -> List[str]:
        task = project.get_task(action.target_task_id or "")
        new_status_str = action.parameters.get("new_status")
        if not task:
            raise ValueError(f"Task '{action.target_task_id}' not found")
        try:
            new_status = TaskStatus(new_status_str)
        except ValueError:
            raise ValueError(f"Invalid status '{new_status_str}'")
        old_status = task.status
        task.status = new_status
        task.state_revision += 1
        return [f"Changed status of '{task.title}' from {old_status.value} to {new_status.value}"]

    def _update_task_attribute(self, action: ProposedAction, project: Project) -> List[str]:
        task = project.get_task(action.target_task_id or "")
        if not task:
            raise ValueError(f"Task '{action.target_task_id}' not found")
        attribute = action.parameters.get("attribute")
        value = action.parameters.get("value")
        allowed_attributes = {"description", "title", "tags", "blocker_reason"}
        if attribute not in allowed_attributes:
            raise ValueError(f"Attribute '{attribute}' is not an allowed mutable attribute")
        old = getattr(task, attribute, None)
        setattr(task, attribute, value)
        task.state_revision += 1
        return [f"Updated '{task.title}'.{attribute}: '{old}' → '{value}'"]

    def _recompute_statuses(self, project: Project) -> None:
        """After execution, recompute task statuses based on new dependency state."""
        from app.services.graph_engine import GraphEngine
        engine = GraphEngine()
        analysis = engine.analyse(project)

        completed = {t.task_id for t in project.tasks if t.status == TaskStatus.COMPLETED}

        for task in project.tasks:
            if task.status == TaskStatus.COMPLETED:
                continue
            if task.task_id in analysis.tasks_ready:
                if task.status == TaskStatus.BLOCKED:
                    task.status = TaskStatus.READY
                    task.blocker_reason = None
                    task.state_revision += 1
            elif task.task_id in analysis.tasks_in_cycles:
                task.status = TaskStatus.BLOCKED
                if not task.blocker_reason:
                    task.blocker_reason = "Part of circular dependency"
                task.state_revision += 1
            else:
                unmet = [d for d in task.dependencies if d not in completed]
                if unmet and task.status not in (TaskStatus.IN_PROGRESS,):
                    task.status = TaskStatus.BLOCKED
                    task.state_revision += 1
