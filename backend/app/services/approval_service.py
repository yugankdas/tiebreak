"""Organization-aware approval routing service for TIEBREAK."""
from __future__ import annotations
from typing import Any, Dict, List, Optional, Tuple
from app.models.project import Project, ResolutionProposal, ProposedAction, ConstraintType
from app.models.organization import (
    ApprovalRequest, ApprovalRequestStatus, Organization, UserProfile, Role
)


class ApprovalRoutingService:
    """
    Determines and enforces authorized approvers for proposed resolutions
    based on organization policies, roles, task ownership, and security requirements.
    """

    def __init__(self):
        self._organizations: Dict[str, Organization] = {}
        self._users: Dict[str, UserProfile] = {}
        self._requests: Dict[str, ApprovalRequest] = {}  # request_id -> ApprovalRequest
        self._seed_data()

    def _seed_data(self):
        # Demo organization
        org = Organization(org_id="org-nova", name="Nova Labs, Inc.", slug="nova-labs")
        self._organizations[org.org_id] = org

        # Seed organization members with real identities matching demo_project.json
        users = [
            UserProfile(
                user_id="mem-01",
                name="Alice Chen",
                email="alice@novalabs.internal",
                role=Role.PRODUCT_MANAGER,
                organization_id="org-nova",
                permissions=["approve_scope", "record_decision", "modify_deadline", "approve_reassignment"],
            ),
            UserProfile(
                user_id="mem-02",
                name="Ben Okafor",
                email="ben@novalabs.internal",
                role=Role.LEAD_ENGINEER,
                organization_id="org-nova",
                permissions=["approve_scope", "record_decision", "execute_security_review", "approve_reassignment"],
            ),
            UserProfile(
                user_id="mem-03",
                name="Clara Singh",
                email="clara@novalabs.internal",
                role=Role.TEAM_MEMBER,
                organization_id="org-nova",
                permissions=["record_decision"],
            ),
            UserProfile(
                user_id="mem-04",
                name="David Reyes",
                email="david@novalabs.internal",
                role=Role.TEAM_MEMBER,
                organization_id="org-nova",
                permissions=["record_decision"],
            ),
            UserProfile(
                user_id="mem-05",
                name="Eve Thornton",
                email="eve@novalabs.internal",
                role=Role.SECURITY_REVIEWER,
                organization_id="org-nova",
                permissions=["execute_security_review", "approve_security_change"],
            ),
            UserProfile(
                user_id="usr-admin",
                name="Sarah Jenkins (Admin)",
                email="admin@novalabs.internal",
                role=Role.ORG_ADMIN,
                organization_id="org-nova",
                permissions=["manage_org", "configure_routing", "admin_override"],
            ),
            # Cross-organization test user
            UserProfile(
                user_id="usr-external",
                name="External Auditor",
                email="auditor@externalcorp.com",
                role=Role.TEAM_MEMBER,
                organization_id="org-other",
                permissions=[],
            ),
        ]
        for u in users:
            self._users[u.user_id] = u

    def get_user(self, user_id: str) -> Optional[UserProfile]:
        return self._users.get(user_id)

    def list_users(self, org_id: Optional[str] = "org-nova") -> List[UserProfile]:
        if not org_id:
            return list(self._users.values())
        return [u for u in self._users.values() if u.organization_id == org_id]

    def route_proposal(
        self,
        proposal: ResolutionProposal,
        project: Project,
        requester_id: str = "mem-01",
    ) -> ApprovalRequest:
        """
        Determines the designated authorized approver(s) according to organization policy.
        """
        org_id = "org-nova"
        designated_approvers: List[str] = []
        routing_reason: str = ""
        action_types = [a.action_type for a in proposal.proposed_actions]
        affected_tasks = [project.get_task(tid) for tid in proposal.affected_task_ids if project.get_task(tid)]

        # Check for Security-Sensitive changes (e.g. task-07, task-11, task-12 or protected tasks)
        is_security_sensitive = any(
            t and (t.is_protected or "security" in t.tags or "compliance" in t.tags)
            for t in affected_tasks
        )
        for a in proposal.proposed_actions:
            target = project.get_task(a.target_task_id or "")
            if target and (target.is_protected or "security" in target.tags):
                is_security_sensitive = True

        if is_security_sensitive:
            # Route to Security Reviewer (Eve Thornton, mem-05)
            designated_approvers = [u.user_id for u in self._users.values() if u.role == Role.SECURITY_REVIEWER and u.organization_id == org_id]
            routing_reason = "Security-sensitive task modification requires mandatory sign-off from designated Security Reviewer."

        elif "approve_provisional_scope" in action_types or "modify_dependency" in action_types:
            # Check explicit permission constraints in project
            allowed_approvers = []
            for c in project.constraints:
                if c.constraint_type == ConstraintType.PERMISSION and c.is_active:
                    allowed_approvers = (c.value or {}).get("allowed_approvers", [])

            if allowed_approvers:
                designated_approvers = [aid for aid in allowed_approvers if aid in self._users]
                routing_reason = f"Provisional scope modification governed by project constraint (Authorized: {', '.join(designated_approvers)})."
            else:
                # Route to Product Manager or Lead Engineer
                designated_approvers = [u.user_id for u in self._users.values() if u.role in (Role.PRODUCT_MANAGER, Role.LEAD_ENGINEER) and u.organization_id == org_id]
                routing_reason = "Scope and dependency modifications require Product Manager or Lead Engineer authorization."

        elif "record_decision" in action_types:
            # Route to decision owner or Product Manager
            designated_approvers = [u.user_id for u in self._users.values() if u.role == Role.PRODUCT_MANAGER and u.organization_id == org_id]
            routing_reason = "Business pricing model and product decisions route to Product Manager."

        elif "reassign_task" in action_types:
            # Route to Lead Engineer
            designated_approvers = [u.user_id for u in self._users.values() if u.role == Role.LEAD_ENGINEER and u.organization_id == org_id]
            routing_reason = "Workforce allocation and task reassignment route to Lead Engineer."

        else:
            # General project changes route to PM
            designated_approvers = [u.user_id for u in self._users.values() if u.role == Role.PRODUCT_MANAGER and u.organization_id == org_id]
            routing_reason = "General workflow coordination routed to Product Manager."

        status = ApprovalRequestStatus.PENDING if designated_approvers else ApprovalRequestStatus.NEEDS_ROUTING

        req = ApprovalRequest(
            org_id=org_id,
            project_id=project.project_id,
            resolution_id=proposal.resolution_id,
            requester_id=requester_id,
            designated_approver_ids=designated_approvers,
            action_type=", ".join(set(action_types)),
            proposed_change=proposal.title,
            rationale=proposal.description,
            affected_task_ids=proposal.affected_task_ids,
            expected_impact=f"Effort: {proposal.estimated_effort_hours}h, Deadline impact: {proposal.deadline_impact_days}d",
            risks=proposal.risks,
            status=status,
            routing_reason=routing_reason or "Routing policy determined by organization hierarchy.",
            project_revision_at_creation=project.revision,
        )
        self._requests[req.request_id] = req
        return req

    def get_requests_for_user(self, user_id: str, org_id: str = "org-nova") -> List[ApprovalRequest]:
        user = self._users.get(user_id)
        if not user or user.organization_id != org_id:
            return []
        
        # Org admins see all requests in their org
        if user.role == Role.ORG_ADMIN:
            return [r for r in self._requests.values() if r.org_id == org_id]
            
        # Approvers see requests where they are designated, plus requests they submitted
        return [
            r for r in self._requests.values()
            if r.org_id == org_id and (user_id in r.designated_approver_ids or r.requester_id == user_id)
        ]

    def get_request(self, request_id: str) -> Optional[ApprovalRequest]:
        return self._requests.get(request_id)

    def get_request_by_resolution(self, resolution_id: str) -> Optional[ApprovalRequest]:
        for r in self._requests.values():
            if r.resolution_id == resolution_id:
                return r
        return None

    def decide_request(
        self,
        request_id: str,
        user_id: str,
        decision: str,  # "APPROVED" or "REJECTED"
        explanation: str = "",
        current_project_revision: int = 0,
    ) -> Tuple[bool, str, Optional[ApprovalRequest]]:
        """
        Validates authorization, cross-organization bounds, self-approval policy,
        and project revision currency.
        """
        req = self._requests.get(request_id)
        if not req:
            return False, "Approval request not found", None

        user = self._users.get(user_id)
        if not user:
            return False, f"User '{user_id}' not found", None

        # Cross-organization security enforcement
        if user.organization_id != req.org_id:
            return False, f"Unauthorized: User belongs to '{user.organization_id}', request belongs to '{req.org_id}'", None

        # Authorization check: must be a designated approver or Org Admin
        if user.role != Role.ORG_ADMIN and user_id not in req.designated_approver_ids:
            return False, f"Access denied: {user.name} ({user.role.value}) is not an authorized approver for this request", None

        # Self-approval restriction for non-admins
        if user_id == req.requester_id and user.role != Role.ORG_ADMIN and len(req.designated_approver_ids) > 1:
            return False, "Self-approval policy violation: You cannot approve your own proposal", None

        # Stale state check
        if current_project_revision != req.project_revision_at_creation:
            req.status = ApprovalRequestStatus.EXPIRED
            return False, f"Stale proposal: Project revision changed from {req.project_revision_at_creation} to {current_project_revision}. Please re-synthesize.", None

        from datetime import datetime
        if decision == "APPROVED":
            req.status = ApprovalRequestStatus.APPROVED
        else:
            req.status = ApprovalRequestStatus.REJECTED

        req.decision_maker_id = user_id
        req.decided_at = datetime.utcnow()
        req.explanation = explanation
        return True, f"Request successfully {req.status.value}", req
