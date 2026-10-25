"""Core domain models for TIEBREAK."""
from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import uuid


def new_id() -> str:
    return str(uuid.uuid4())


# ─────────────────────────────── Enums ────────────────────────────────────────

class TaskStatus(str, Enum):
    NOT_STARTED = "NOT_STARTED"
    READY = "READY"
    IN_PROGRESS = "IN_PROGRESS"
    BLOCKED = "BLOCKED"
    COMPLETED = "COMPLETED"


class ProjectStatus(str, Enum):
    ON_TRACK = "ON_TRACK"
    AT_RISK = "AT_RISK"
    BLOCKED = "BLOCKED"
    COMPLETED = "COMPLETED"


class BlockerType(str, Enum):
    CIRCULAR_DEPENDENCY = "CIRCULAR_DEPENDENCY"
    INCOMPLETE_PREREQUISITE = "INCOMPLETE_PREREQUISITE"
    MISSING_DECISION = "MISSING_DECISION"
    RESOURCE_CONFLICT = "RESOURCE_CONFLICT"
    DEADLINE_RISK = "DEADLINE_RISK"
    MANDATORY_REVIEW = "MANDATORY_REVIEW"


class BlockerSeverity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


class BlockerStatus(str, Enum):
    ACTIVE = "ACTIVE"
    RESOLVED = "RESOLVED"
    PARTIALLY_RESOLVED = "PARTIALLY_RESOLVED"


class ConstraintType(str, Enum):
    HARD = "HARD"
    SOFT = "SOFT"
    DEADLINE = "DEADLINE"
    RESOURCE_LIMIT = "RESOURCE_LIMIT"
    MANDATORY_REVIEW = "MANDATORY_REVIEW"
    PROTECTED_DEPENDENCY = "PROTECTED_DEPENDENCY"
    PERMISSION = "PERMISSION"
    EVIDENCE_REQUIRED = "EVIDENCE_REQUIRED"


class ValidationResult(str, Enum):
    PASS = "PASS"
    FAIL = "FAIL"
    NEEDS_INFORMATION = "NEEDS_INFORMATION"


class ApprovalState(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"


class ExecutionState(str, Enum):
    NOT_EXECUTED = "NOT_EXECUTED"
    EXECUTING = "EXECUTING"
    EXECUTED = "EXECUTED"
    FAILED = "FAILED"


class VerificationState(str, Enum):
    NOT_VERIFIED = "NOT_VERIFIED"
    VERIFIED_RESOLVED = "VERIFIED_RESOLVED"
    PARTIALLY_RESOLVED = "PARTIALLY_RESOLVED"
    NOT_RESOLVED = "NOT_RESOLVED"
    NEW_BLOCKER_DETECTED = "NEW_BLOCKER_DETECTED"
    VERIFICATION_FAILED = "VERIFICATION_FAILED"


class ResolutionStrategy(str, Enum):
    PROVISIONAL_SCOPE = "PROVISIONAL_SCOPE"
    REDUCED_SCOPE = "REDUCED_SCOPE"
    DEPENDENCY_REMOVAL = "DEPENDENCY_REMOVAL"
    RESOURCE_REALLOCATION = "RESOURCE_REALLOCATION"
    DECISION_ESCALATION = "DECISION_ESCALATION"
    PARALLEL_TRACK = "PARALLEL_TRACK"


class AuditAction(str, Enum):
    BLOCKER_DETECTED = "BLOCKER_DETECTED"
    RESOLUTION_GENERATED = "RESOLUTION_GENERATED"
    RESOLUTION_VALIDATED = "RESOLUTION_VALIDATED"
    RESOLUTION_APPROVED = "RESOLUTION_APPROVED"
    RESOLUTION_REJECTED = "RESOLUTION_REJECTED"
    ACTION_EXECUTED = "ACTION_EXECUTED"
    STATE_CHANGED = "STATE_CHANGED"
    VERIFICATION_COMPLETED = "VERIFICATION_COMPLETED"
    FAILPROOF_EVENT = "FAILPROOF_EVENT"
    PROJECT_RESET = "PROJECT_RESET"


# ─────────────────────────── Sub-models ───────────────────────────────────────

class TeamMember(BaseModel):
    member_id: str = Field(default_factory=new_id)
    name: str
    role: str
    available_capacity: float  # hours per week
    skills: List[str] = Field(default_factory=list)
    permissions: List[str] = Field(default_factory=list)
    current_assignments: List[str] = Field(default_factory=list)  # task IDs


class Constraint(BaseModel):
    constraint_id: str = Field(default_factory=new_id)
    constraint_type: ConstraintType
    description: str
    applies_to: Optional[List[str]] = None  # task IDs or member IDs
    value: Optional[Any] = None  # e.g., resource limit number
    is_active: bool = True


class Task(BaseModel):
    task_id: str = Field(default_factory=new_id)
    title: str
    description: str
    status: TaskStatus = TaskStatus.NOT_STARTED
    priority: int = 3  # 1=highest
    owner_id: Optional[str] = None
    estimated_effort_hours: float = 0
    dependencies: List[str] = Field(default_factory=list)  # task IDs
    deadline: Optional[datetime] = None
    required_skills: List[str] = Field(default_factory=list)
    completion_evidence: Optional[str] = None
    is_protected: bool = False  # hard constraint: cannot be removed
    dependencies_mutable: bool = True
    state_revision: int = 0
    tags: List[str] = Field(default_factory=list)
    blocker_reason: Optional[str] = None


class Blocker(BaseModel):
    blocker_id: str = Field(default_factory=new_id)
    blocker_type: BlockerType
    title: str
    explanation: str
    affected_task_ids: List[str]
    root_cause: str
    evidence: List[str] = Field(default_factory=list)
    downstream_impact: List[str] = Field(default_factory=list)
    severity: BlockerSeverity = BlockerSeverity.HIGH
    detected_at: datetime = Field(default_factory=datetime.utcnow)
    status: BlockerStatus = BlockerStatus.ACTIVE
    cycle_nodes: Optional[List[str]] = None  # for circular dependencies


class ConstraintCheckResult(BaseModel):
    constraint_id: str
    constraint_type: ConstraintType
    rule: str
    result: ValidationResult
    evidence: str
    is_hard_constraint: bool = False


class ProposedAction(BaseModel):
    action_type: str
    description: str
    target_task_id: Optional[str] = None
    target_member_id: Optional[str] = None
    parameters: Dict[str, Any] = Field(default_factory=dict)


class ResolutionProposal(BaseModel):
    resolution_id: str = Field(default_factory=new_id)
    blocker_id: str
    project_id: str
    title: str
    strategy: ResolutionStrategy
    description: str
    proposed_actions: List[ProposedAction] = Field(default_factory=list)
    supporting_evidence: List[str] = Field(default_factory=list)
    assumptions: List[str] = Field(default_factory=list)
    expected_benefits: List[str] = Field(default_factory=list)
    risks: List[str] = Field(default_factory=list)
    trade_offs: List[str] = Field(default_factory=list)
    affected_task_ids: List[str] = Field(default_factory=list)
    estimated_effort_hours: float = 0
    deadline_impact_days: int = 0
    resource_impact: str = "None"
    constraint_checks: List[ConstraintCheckResult] = Field(default_factory=list)
    score: Optional[float] = None
    score_explanation: Optional[str] = None
    approval_state: ApprovalState = ApprovalState.PENDING
    execution_state: ExecutionState = ExecutionState.NOT_EXECUTED
    verification_state: VerificationState = VerificationState.NOT_VERIFIED
    project_revision: int = 0
    is_feasible: bool = True
    infeasibility_reason: Optional[str] = None
    is_fallback: bool = False  # True if generated by deterministic fallback
    created_at: datetime = Field(default_factory=datetime.utcnow)
    approved_at: Optional[datetime] = None
    executed_at: Optional[datetime] = None
    approval_request_id: Optional[str] = None
    designated_approver_ids: List[str] = Field(default_factory=list)
    routing_reason: Optional[str] = None


class ExecutionResult(BaseModel):
    success: bool
    actions_attempted: List[Dict[str, Any]] = Field(default_factory=list)
    actions_succeeded: List[Dict[str, Any]] = Field(default_factory=list)
    actions_failed: List[Dict[str, Any]] = Field(default_factory=list)
    state_changes: List[str] = Field(default_factory=list)
    error: Optional[str] = None
    executed_at: datetime = Field(default_factory=datetime.utcnow)


class VerificationResult(BaseModel):
    verification_state: VerificationState
    original_blocker_resolved: bool
    tasks_now_ready: List[str] = Field(default_factory=list)
    tasks_still_blocked: List[str] = Field(default_factory=list)
    new_blockers: List[str] = Field(default_factory=list)
    evidence: List[str] = Field(default_factory=list)
    verified_at: datetime = Field(default_factory=datetime.utcnow)


class AuditEvent(BaseModel):
    event_id: str = Field(default_factory=new_id)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    actor: str = "system"
    action: AuditAction
    target: str
    input_summary: str
    outcome: str
    validation_results: Optional[List[ConstraintCheckResult]] = None
    error_details: Optional[str] = None
    previous_revision: Optional[int] = None
    resulting_revision: Optional[int] = None


class Project(BaseModel):
    project_id: str = Field(default_factory=new_id)
    name: str
    description: str
    status: ProjectStatus = ProjectStatus.ON_TRACK
    start_date: datetime = Field(default_factory=datetime.utcnow)
    deadline: datetime
    team_members: List[TeamMember] = Field(default_factory=list)
    tasks: List[Task] = Field(default_factory=list)
    constraints: List[Constraint] = Field(default_factory=list)
    revision: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
    updated_at: datetime = Field(default_factory=datetime.utcnow)

    def get_task(self, task_id: str) -> Optional[Task]:
        for t in self.tasks:
            if t.task_id == task_id:
                return t
        return None

    def get_member(self, member_id: str) -> Optional[TeamMember]:
        for m in self.team_members:
            if m.member_id == member_id:
                return m
        return None
