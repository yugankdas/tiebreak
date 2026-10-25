"""Automated test suite for TIEBREAK deadlock detection, resolution, and Groq integration."""
import unittest
import os
from unittest.mock import MagicMock, patch

from app.services.graph_engine import GraphEngine
from app.services.deadlock_detector import DeadlockDetector
from app.services.constraint_validator import ConstraintValidator
from app.services.action_executor import ActionExecutor
from app.services.outcome_verifier import OutcomeVerifier
from app.services.groq_provider import GroqProvider
from app.services.resolution_generator import ResolutionGenerator
from app.models.project import (
    Project, Task, TeamMember, Constraint, TaskStatus, BlockerType,
    ResolutionProposal, ProposedAction, ResolutionStrategy, ApprovalState
)


class TestTiebreak(unittest.TestCase):

    def setUp(self):
        self.engine = GraphEngine()
        self.detector = DeadlockDetector(self.engine)
        self.validator = ConstraintValidator()
        self.tasks = [
            Task(
                task_id="t1",
                title="Task 1",
                description="desc",
                status=TaskStatus.BLOCKED,
                priority=1,
                owner_id="m1",
                estimated_effort_hours=10,
                dependencies=["t2"],
                deadline=None,
                required_skills=[],
                completion_evidence=None,
                is_protected=False,
                dependencies_mutable=True,
                state_revision=0,
                tags=[],
                blocker_reason=None
            ),
            Task(
                task_id="t2",
                title="Task 2",
                description="desc",
                status=TaskStatus.BLOCKED,
                priority=1,
                owner_id="m1",
                estimated_effort_hours=10,
                dependencies=["t1"],
                deadline=None,
                required_skills=[],
                completion_evidence=None,
                is_protected=False,
                dependencies_mutable=True,
                state_revision=0,
                tags=[],
                blocker_reason=None
            )
        ]
        self.project = Project(
            project_id="test-proj",
            name="Test",
            description="desc",
            deadline="2026-12-01T00:00:00",
            team_members=[],
            tasks=self.tasks,
            constraints=[],
            revision=0,
        )

    def test_circular_dependency_detection(self):
        blockers = self.detector.detect_all(self.project)
        cycles = [b for b in blockers if b.blocker_type == BlockerType.CIRCULAR_DEPENDENCY]
        self.assertEqual(len(cycles), 1)
        self.assertEqual(set(cycles[0].cycle_nodes), {"t1", "t2"})

    def test_protected_constraint_preservation(self):
        prot_task = Task(
            task_id="t-prot",
            title="Security Review",
            description="desc",
            status=TaskStatus.NOT_STARTED,
            priority=1,
            owner_id="m1",
            estimated_effort_hours=5,
            dependencies=[],
            deadline=None,
            required_skills=[],
            completion_evidence=None,
            is_protected=True,
            dependencies_mutable=False,
            state_revision=0,
            tags=["mandatory"],
            blocker_reason=None
        )
        self.assertTrue(prot_task.is_protected)
        self.assertFalse(prot_task.dependencies_mutable)

    def test_groq_missing_api_key_status(self):
        with patch.dict(os.environ, {"GROQ_API_KEY": ""}, clear=True):
            provider = GroqProvider()
            status = provider.test_connection()
            self.assertFalse(status["configured"])
            self.assertFalse(status["connected"])
            self.assertEqual(status["status"], "NOT_CONFIGURED")

    def test_groq_invalid_api_key_status(self):
        with patch.dict(os.environ, {"GROQ_API_KEY": "gsk_invalid_test_dummy"}, clear=True):
            provider = GroqProvider()
            status = provider.test_connection()
            self.assertTrue(status["configured"])
            self.assertFalse(status["connected"])
            self.assertIn(status["status"], ["AUTHENTICATION_FAILED", "CONNECTION_ERROR"])

    def test_fallback_resolution_generation(self):
        with patch.dict(os.environ, {"GROQ_API_KEY": ""}, clear=True):
            provider = GroqProvider()
            generator = ResolutionGenerator(provider)
            blockers = self.detector.detect_all(self.project)
            proposals = generator.generate(blockers[0], self.project)
            self.assertGreater(len(proposals), 0)
            self.assertTrue(all(p.is_fallback for p in proposals))

    def test_prohibited_action_rejection(self):
        executor = ActionExecutor(self.validator)
        invalid_action = ProposedAction(
            action_type="arbitrary_bash_command",
            description="Run rm -rf",
            parameters={"cmd": "echo hack"},
        )
        proposal = ResolutionProposal(
            blocker_id="b1",
            project_id="test-proj",
            title="Malicious Proposal",
            strategy=ResolutionStrategy.DEPENDENCY_REMOVAL,
            description="Test injection",
            proposed_actions=[invalid_action],
            approval_state=ApprovalState.APPROVED,
        )
        result = executor.execute(proposal, self.project)
        self.assertFalse(result.success)
        self.assertIn("not in the allowlist", result.error or "")


if __name__ == "__main__":
    unittest.main()
