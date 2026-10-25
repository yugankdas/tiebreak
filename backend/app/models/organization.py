"""Organization, Role, and Approval Routing models for TIEBREAK."""
from __future__ import annotations
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field
import uuid


def new_id() -> str:
    return str(uuid.uuid4())


class Role(str, Enum):
    ORG_ADMIN = "ORG_ADMIN"
    PRODUCT_MANAGER = "PRODUCT_MANAGER"
    LEAD_ENGINEER = "LEAD_ENGINEER"
    SECURITY_REVIEWER = "SECURITY_REVIEWER"
    TEAM_MEMBER = "TEAM_MEMBER"


class ApprovalRequestStatus(str, Enum):
    PENDING = "PENDING"
    APPROVED = "APPROVED"
    REJECTED = "REJECTED"
    NEEDS_ROUTING = "NEEDS_ROUTING"
    EXPIRED = "EXPIRED"
    CANCELLED = "CANCELLED"


class UserProfile(BaseModel):
    user_id: str
    name: str
    email: str
    role: Role
    organization_id: str
    permissions: List[str] = Field(default_factory=list)


class Organization(BaseModel):
    org_id: str
    name: str
    slug: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class ApprovalRequest(BaseModel):
    request_id: str = Field(default_factory=new_id)
    org_id: str
    project_id: str
    resolution_id: str
    requester_id: str
    designated_approver_ids: List[str] = Field(default_factory=list)
    action_type: str
    proposed_change: str
    rationale: str
    affected_task_ids: List[str] = Field(default_factory=list)
    expected_impact: str
    risks: List[str] = Field(default_factory=list)
    status: ApprovalRequestStatus = ApprovalRequestStatus.PENDING
    decision_maker_id: Optional[str] = None
    decided_at: Optional[datetime] = None
    explanation: Optional[str] = None
    routing_reason: str = ""
    project_revision_at_creation: int = 0
    created_at: datetime = Field(default_factory=datetime.utcnow)
