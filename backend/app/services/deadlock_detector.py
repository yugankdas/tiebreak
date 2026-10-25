"""Deterministic blocker detection — no LLM involved."""
from __future__ import annotations
from datetime import datetime
from typing import Dict, List, Optional
import uuid

from app.models.project import (
    Blocker, BlockerType, BlockerSeverity, BlockerStatus,
    Project, TaskStatus,
)
from app.services.graph_engine import GraphEngine, GraphAnalysis


class DeadlockDetector:
    def __init__(self, engine: GraphEngine):
        self.engine = engine

    def detect_all(self, project: Project) -> List[Blocker]:
        analysis = self.engine.analyse(project)
        blockers: List[Blocker] = []

        blockers.extend(self._detect_circular_dependencies(project, analysis))
        blockers.extend(self._detect_missing_decisions(project))
        blockers.extend(self._detect_resource_conflicts(project))
        blockers.extend(self._detect_deadline_risks(project, analysis))
        blockers.extend(self._detect_mandatory_review_blockers(project, analysis))

        return blockers

    # ── circular dependencies ──────────────────────────────────────────────────

    def _detect_circular_dependencies(self, project: Project, analysis: GraphAnalysis) -> List[Blocker]:
        results = []
        task_map = {t.task_id: t for t in project.tasks}

        for cycle in analysis.cycles:
            cycle_titles = [task_map[tid].title for tid in cycle if tid in task_map]
            downstream = set()
            for tid in cycle:
                downstream.update(analysis.downstream_map.get(tid, []))
            downstream -= set(cycle)
            downstream_titles = [task_map[tid].title for tid in downstream if tid in task_map]

            evidence = [
                f"Cycle detected: {' → '.join(cycle + [cycle[0]])}",
                f"Tasks involved: {', '.join(cycle_titles)}",
            ]
            for tid in cycle:
                task = task_map.get(tid)
                if task:
                    evidence.append(
                        f"FACT: '{task.title}' (task {tid}) depends on: "
                        f"{', '.join(task.dependencies)}"
                    )

            b = Blocker(
                blocker_id=f"blk-cycle-{'-'.join(sorted(cycle)[:2])}",
                blocker_type=BlockerType.CIRCULAR_DEPENDENCY,
                title=f"Circular Dependency: {' ↔ '.join(cycle_titles[:3])}",
                explanation=(
                    f"A circular dependency prevents {len(cycle)} tasks from progressing. "
                    f"Each task in the cycle requires another task in the same cycle to complete first, "
                    f"creating a deadlock. No task in this cycle can become READY through normal prerequisite paths."
                ),
                affected_task_ids=cycle,
                root_cause=(
                    "The dependency chain forms a loop with no external entry point. "
                    "At least one dependency in the cycle must be modified, made provisional, or removed "
                    "before any task in the cycle can progress."
                ),
                evidence=evidence,
                downstream_impact=list(downstream),
                severity=BlockerSeverity.CRITICAL,
                cycle_nodes=cycle,
            )
            results.append(b)

        return results

    # ── missing decisions ──────────────────────────────────────────────────────

    def _detect_missing_decisions(self, project: Project) -> List[Blocker]:
        results = []
        task_map = {t.task_id: t for t in project.tasks}
        member_map = {m.member_id: m.name for m in project.team_members}

        decision_tasks = [
            t for t in project.tasks
            if "decision" in t.tags or "unresolved" in t.tags
        ]

        for task in decision_tasks:
            dependents = [
                t for t in project.tasks
                if task.task_id in t.dependencies
            ]
            if not dependents and task.status == TaskStatus.BLOCKED:
                dependents = []  # still report as missing decision

            owner = member_map.get(task.owner_id or "", "Unknown")
            b = Blocker(
                blocker_id=f"blk-decision-{task.task_id}",
                blocker_type=BlockerType.MISSING_DECISION,
                title=f"Unresolved Decision: {task.title}",
                explanation=(
                    f"The task '{task.title}' (owner: {owner}) represents an unresolved decision. "
                    f"{task.description} "
                    f"This blocks {len(dependents)} downstream task(s)."
                ),
                affected_task_ids=[task.task_id] + [t.task_id for t in dependents],
                root_cause=task.blocker_reason or "Decision has not been reached or recorded.",
                evidence=[
                    f"FACT: Task '{task.title}' is tagged 'decision'/'unresolved'",
                    f"FACT: Task status is {task.status.value}",
                    f"FACT: {len(dependents)} tasks depend on this task: "
                    f"{', '.join(t.title for t in dependents)}",
                    f"INFERENCE: Until this decision is recorded, dependent tasks cannot proceed",
                ],
                downstream_impact=[t.task_id for t in dependents],
                severity=BlockerSeverity.HIGH,
            )
            results.append(b)

        return results

    # ── resource conflicts ─────────────────────────────────────────────────────

    def _detect_resource_conflicts(self, project: Project) -> List[Blocker]:
        results = []

        for member in project.team_members:
            # sum effort of assigned active tasks
            assigned_tasks = [
                t for t in project.tasks
                if t.owner_id == member.member_id
                and t.status not in (TaskStatus.COMPLETED,)
            ]
            total_effort = sum(t.estimated_effort_hours for t in assigned_tasks)
            # rough capacity check: 1 week window
            weekly_capacity = member.available_capacity
            # if total effort > 2x weekly capacity, flag
            if total_effort > weekly_capacity * 2:
                b = Blocker(
                    blocker_id=f"blk-resource-{member.member_id}",
                    blocker_type=BlockerType.RESOURCE_CONFLICT,
                    title=f"Resource Overcommitment: {member.name}",
                    explanation=(
                        f"{member.name} ({member.role}) is assigned {total_effort:.0f} hours of work "
                        f"across {len(assigned_tasks)} active tasks, but has only "
                        f"{weekly_capacity} hours/week available. "
                        f"This creates a bottleneck and risks delayed delivery."
                    ),
                    affected_task_ids=[t.task_id for t in assigned_tasks],
                    root_cause=(
                        f"Task load exceeds available capacity by "
                        f"{total_effort - weekly_capacity:.0f} hours "
                        f"(assuming tasks run sequentially in one week)."
                    ),
                    evidence=[
                        f"FACT: {member.name} available capacity: {weekly_capacity} h/week",
                        f"FACT: Total assigned effort: {total_effort:.0f} hours",
                        f"FACT: Assigned tasks: {', '.join(t.title for t in assigned_tasks)}",
                        f"INFERENCE: At least {total_effort / max(weekly_capacity,1):.1f}x overcommitted",
                    ],
                    downstream_impact=[],
                    severity=BlockerSeverity.MEDIUM,
                )
                results.append(b)

        return results

    # ── deadline risks ─────────────────────────────────────────────────────────

    def _detect_deadline_risks(self, project: Project, analysis: GraphAnalysis) -> List[Blocker]:
        results = []
        now = datetime.utcnow()
        project_deadline = project.deadline

        at_risk = []
        for task in project.tasks:
            if task.status == TaskStatus.COMPLETED:
                continue
            # tasks past their own deadline or very close
            if task.deadline and task.deadline < now:
                at_risk.append((task, "already past deadline"))
            elif task.deadline and (task.deadline - now).days <= 3:
                at_risk.append((task, "deadline within 3 days"))

        if at_risk:
            affected_ids = [t.task_id for t, _ in at_risk]
            evidence = []
            for task, reason in at_risk:
                evidence.append(
                    f"FACT: '{task.title}' — {reason}: "
                    f"{task.deadline.date() if task.deadline else 'no deadline'}"
                )

            b = Blocker(
                blocker_id="blk-deadline-risk",
                blocker_type=BlockerType.DEADLINE_RISK,
                title=f"Deadline Risk: {len(at_risk)} Task(s) at Risk",
                explanation=(
                    f"{len(at_risk)} task(s) are past their deadline or critically close. "
                    f"Given existing blockers, they cannot currently progress."
                ),
                affected_task_ids=affected_ids,
                root_cause="Tasks are overdue or at imminent risk due to upstream blockage.",
                evidence=evidence,
                downstream_impact=[],
                severity=BlockerSeverity.HIGH,
            )
            results.append(b)

        return results

    # ── mandatory review blockers ──────────────────────────────────────────────

    def _detect_mandatory_review_blockers(self, project: Project, analysis: GraphAnalysis) -> List[Blocker]:
        results = []
        task_map = {t.task_id: t for t in project.tasks}

        # Find protected tasks that are not yet completed
        protected_incomplete = [t for t in project.tasks if t.is_protected and t.status != TaskStatus.COMPLETED]

        for task in protected_incomplete:
            # Find tasks that directly or indirectly depend on this
            downstream = [
                t for t in project.tasks
                if task.task_id in t.dependencies
                and t.status != TaskStatus.COMPLETED
            ]
            if not downstream:
                continue

            b = Blocker(
                blocker_id=f"blk-review-{task.task_id}",
                blocker_type=BlockerType.MANDATORY_REVIEW,
                title=f"Mandatory Review Pending: {task.title}",
                explanation=(
                    f"'{task.title}' is a mandatory protected task that has not been completed. "
                    f"{len(downstream)} downstream task(s) cannot proceed until this is done. "
                    f"This task cannot be bypassed or removed from the dependency chain."
                ),
                affected_task_ids=[task.task_id] + [t.task_id for t in downstream],
                root_cause=f"Protected task '{task.title}' is not yet completed.",
                evidence=[
                    f"FACT: '{task.title}' is marked is_protected=true",
                    f"FACT: Current status: {task.status.value}",
                    f"FACT: Downstream tasks waiting: {', '.join(t.title for t in downstream)}",
                    f"CONSTRAINT: This task's dependency chain cannot be modified",
                ],
                downstream_impact=[t.task_id for t in downstream],
                severity=BlockerSeverity.HIGH,
            )
            results.append(b)

        return results
