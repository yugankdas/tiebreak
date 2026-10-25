"""Organization and Approval Routing API endpoints."""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

from app.dependencies import get_approval_service, get_project_service
from app.models.organization import ApprovalRequest, UserProfile
from app.services.approval_service import ApprovalRoutingService
from app.services.project_service import ProjectService

router = APIRouter(tags=["organization-approvals"])


class DecisionPayload(BaseModel):
    user_id: str
    decision: str  # "APPROVED" or "REJECTED"
    explanation: Optional[str] = ""


@router.get("/users", response_model=List[UserProfile])
async def list_users(
    org_id: str = "org-nova",
    approvals_svc: ApprovalRoutingService = Depends(get_approval_service),
):
    """List members of the organization with their roles and permissions."""
    return approvals_svc.list_users(org_id)


@router.get("/inbox", response_model=List[ApprovalRequest])
async def get_user_inbox(
    user_id: str = Query(..., description="ID of the user viewing their inbox"),
    org_id: str = "org-nova",
    approvals_svc: ApprovalRoutingService = Depends(get_approval_service),
):
    """Fetch pending and decided approval requests scoped to the authenticated user."""
    return approvals_svc.get_requests_for_user(user_id=user_id, org_id=org_id)


@router.get("/requests/{request_id}", response_model=ApprovalRequest)
async def get_approval_request(
    request_id: str,
    approvals_svc: ApprovalRoutingService = Depends(get_approval_service),
):
    req = approvals_svc.get_request(request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Approval request not found")
    return req


@router.post("/requests/{request_id}/decide", response_model=ApprovalRequest)
async def decide_approval_request(
    request_id: str,
    payload: DecisionPayload,
    approvals_svc: ApprovalRoutingService = Depends(get_approval_service),
    project_svc: ProjectService = Depends(get_project_service),
):
    """
    Submits an official approval or rejection decision.
    Validates user authorization, role policies, organization boundaries, and project currency.
    """
    req = approvals_svc.get_request(request_id)
    if not req:
        raise HTTPException(status_code=404, detail="Approval request not found")

    project = project_svc.get_project(req.project_id)
    curr_rev = project.revision if project else 0

    ok, msg, updated_req = approvals_svc.decide_request(
        request_id=request_id,
        user_id=payload.user_id,
        decision=payload.decision,
        explanation=payload.explanation or "",
        current_project_revision=curr_rev,
    )

    if not ok:
        raise HTTPException(status_code=403, detail=msg)

    # Sync project service resolution state
    if payload.decision == "APPROVED":
        project_svc.approve_resolution(
            project_id=req.project_id,
            resolution_id=req.resolution_id,
            actor=payload.user_id,
        )
    else:
        project_svc.reject_resolution(
            project_id=req.project_id,
            resolution_id=req.resolution_id,
            actor=payload.user_id,
            reason=payload.explanation or "",
        )

    return updated_req
