import unittest
from app.services.approval_service import ApprovalRoutingService
from app.models.organization import (
    ApprovalRequestStatus,
    Role
)
from app.models.project import Project, ResolutionProposal, ProposedAction, Task, Constraint, ConstraintType

class TestApprovalRoutingService(unittest.TestCase):
    def setUp(self):
        self.service = ApprovalRoutingService()
        # Create a sample project with security & non-security tasks
        self.project = Project(
            project_id="prj-test",
            name="Test Project",
            description="Test project description",
            deadline="2026-11-01T00:00:00Z",
            revision=1,
            tasks=[
                Task(task_id="task-01", title="API Gateway", description="Core API", status="IN_PROGRESS", assignee="mem-01", tags=["backend"]),
                Task(task_id="task-07", title="Security Review & Audit", description="Security audit", status="BLOCKED", assignee="mem-05", is_protected=True, tags=["security"]),
                Task(task_id="task-03", title="Pricing Engine", description="Pricing calculations", status="BLOCKED", assignee="mem-03", tags=["pricing"]),
            ],
            constraints=[
                Constraint(
                    constraint_id="c-01",
                    constraint_type=ConstraintType.PERMISSION,
                    title="Scope Permission",
                    description="Allowed approvers for scope changes",
                    value={"allowed_approvers": ["mem-01", "mem-02"]},
                    is_active=True
                )
            ]
        )

    def test_seeded_users_and_roles(self):
        """Verify seeded organization users exist with stable IDs and proper roles."""
        users = self.service.list_users(org_id=None)
        users_map = {u.user_id: u for u in users}
        self.assertIn("mem-01", users_map) # Alice Chen (PM)
        self.assertEqual(users_map["mem-01"].role, Role.PRODUCT_MANAGER)
        self.assertIn("mem-02", users_map) # Ben Okafor (Lead Eng)
        self.assertEqual(users_map["mem-02"].role, Role.LEAD_ENGINEER)
        self.assertIn("mem-05", users_map) # Eve Thornton (Security)
        self.assertEqual(users_map["mem-05"].role, Role.SECURITY_REVIEWER)
        self.assertIn("usr-external", users_map) # External Auditor (org-other)
        self.assertEqual(users_map["usr-external"].organization_id, "org-other")

    def test_routing_security_sensitive_action(self):
        """Actions affecting security tasks route specifically to SECURITY_REVIEWER."""
        proposal = ResolutionProposal(
            resolution_id="res-sec-1",
            blocker_id="dl-01",
            project_id="prj-test",
            strategy="DEPENDENCY_REMOVAL",
            title="Update security constraint",
            description="Modify JWT auth flow for security review",
            affected_task_ids=["task-07"],
            proposed_actions=[
                ProposedAction(action_type="modify_dependency", target_task_id="task-07", description="Modify security dependency")
            ],
            requires_human_approval=True
        )
        req = self.service.route_proposal(proposal, self.project, requester_id="mem-01")
        self.assertEqual(req.designated_approver_ids, ["mem-05"])
        self.assertIn("Security Reviewer", req.routing_reason)
        self.assertEqual(req.status, ApprovalRequestStatus.PENDING)

    def test_routing_scope_change_action(self):
        """Scope/Provisional changes route to authorized PM/Lead Engineer according to policy."""
        proposal = ResolutionProposal(
            resolution_id="res-scope-1",
            blocker_id="dl-01",
            project_id="prj-test",
            strategy="PROVISIONAL_SCOPE",
            title="Approve Provisional Schema",
            description="Unblock frontend with provisional API",
            affected_task_ids=["task-01"],
            proposed_actions=[
                ProposedAction(action_type="approve_provisional_scope", target_task_id="task-01", description="Approve provisional API")
            ],
            requires_human_approval=True
        )
        req = self.service.route_proposal(proposal, self.project, requester_id="mem-03")
        self.assertIn("mem-01", req.designated_approver_ids)
        self.assertIn("mem-02", req.designated_approver_ids)
        self.assertIn("Provisional scope", req.routing_reason)

    def test_routing_reassignment_action(self):
        """Task reassignment routes to Lead Engineer."""
        proposal = ResolutionProposal(
            resolution_id="res-reassign-1",
            blocker_id="dl-01",
            project_id="prj-test",
            strategy="RESOURCE_REALLOCATION",
            title="Reassign Task",
            description="Reassign to unblock",
            affected_task_ids=["task-03"],
            proposed_actions=[
                ProposedAction(action_type="reassign_task", target_task_id="task-03", description="Reassign task-03")
            ],
            requires_human_approval=True
        )
        req = self.service.route_proposal(proposal, self.project, requester_id="mem-01")
        self.assertEqual(req.designated_approver_ids, ["mem-02"])
        self.assertIn("Lead Engineer", req.routing_reason)

    def test_decide_request_authorization_enforcement(self):
        """Authorized approver can approve; unauthorized user is rejected; cross-org rejected."""
        proposal = ResolutionProposal(
            resolution_id="res-auth-test",
            blocker_id="dl-01",
            project_id="prj-test",
            strategy="PARALLEL_TRACK",
            title="Test Proposal",
            description="Test authorization",
            affected_task_ids=["task-01"],
            proposed_actions=[
                ProposedAction(action_type="approve_provisional_scope", target_task_id="task-01", description="Approve provisional API")
            ],
            requires_human_approval=True
        )
        req = self.service.route_proposal(proposal, self.project, requester_id="mem-03")

        # 1. Unauthorized attempt by ordinary team member (mem-04)
        success, msg, _ = self.service.decide_request(
            request_id=req.request_id,
            user_id="mem-04",
            decision="APPROVED",
            current_project_revision=1
        )
        self.assertFalse(success)
        self.assertIn("Access denied", msg)

        # 2. Cross-org attempt by external user (usr-external)
        success, msg, _ = self.service.decide_request(
            request_id=req.request_id,
            user_id="usr-external",
            decision="APPROVED",
            current_project_revision=1
        )
        self.assertFalse(success)
        self.assertIn("Unauthorized: User belongs to 'org-other'", msg)

        # 3. Authorized approval by Alice Chen (mem-01, PM)
        success, msg, updated_req = self.service.decide_request(
            request_id=req.request_id,
            user_id="mem-01",
            decision="APPROVED",
            explanation="Approved by PM after review",
            current_project_revision=1
        )
        self.assertTrue(success)
        self.assertEqual(updated_req.status, ApprovalRequestStatus.APPROVED)
        self.assertEqual(updated_req.decision_maker_id, "mem-01")

    def test_stale_project_revision_rejected(self):
        """If project revision changes before approval, decision is rejected as STALE/EXPIRED."""
        proposal = ResolutionProposal(
            resolution_id="res-stale-1",
            blocker_id="dl-01",
            project_id="prj-test",
            strategy="PARALLEL_TRACK",
            title="Stale Proposal",
            description="Testing stale revision rejection",
            affected_task_ids=["task-01"],
            proposed_actions=[
                ProposedAction(action_type="approve_provisional_scope", target_task_id="task-01", description="Approve provisional API")
            ],
            requires_human_approval=True
        )
        req = self.service.route_proposal(proposal, self.project, requester_id="mem-03")
        self.assertEqual(req.project_revision_at_creation, 1)

        # Project was modified (revision bumped to 2)
        success, msg, _ = self.service.decide_request(
            request_id=req.request_id,
            user_id="mem-01",
            decision="APPROVED",
            current_project_revision=2
        )
        self.assertFalse(success)
        self.assertIn("Stale proposal", msg)
        self.assertEqual(req.status, ApprovalRequestStatus.EXPIRED)

if __name__ == '__main__':
    unittest.main()
