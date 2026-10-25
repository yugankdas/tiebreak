"""Audit service — records all significant events."""
from __future__ import annotations
from typing import Dict, List, Optional

from app.models.project import AuditAction, AuditEvent, ConstraintCheckResult


class AuditService:
    def __init__(self):
        self._events: List[AuditEvent] = []

    def record(
        self,
        action: AuditAction,
        target: str,
        input_summary: str,
        outcome: str,
        actor: str = "system",
        validation_results: Optional[List[ConstraintCheckResult]] = None,
        error_details: Optional[str] = None,
        previous_revision: Optional[int] = None,
        resulting_revision: Optional[int] = None,
    ) -> AuditEvent:
        event = AuditEvent(
            actor=actor,
            action=action,
            target=target,
            input_summary=input_summary,
            outcome=outcome,
            validation_results=validation_results,
            error_details=error_details,
            previous_revision=previous_revision,
            resulting_revision=resulting_revision,
        )
        self._events.append(event)
        return event

    def get_all(self) -> List[AuditEvent]:
        return list(reversed(self._events))  # newest first

    def get_for_project(self, project_id: str) -> List[AuditEvent]:
        return [
            e for e in reversed(self._events)
            if project_id in e.target
        ]

    def clear(self) -> None:
        self._events.clear()


_audit = AuditService()


def get_audit_service() -> AuditService:
    return _audit
