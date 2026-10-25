"""Resolution endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import List, Optional

from app.dependencies import get_project_service
from app.models.project import ResolutionProposal
from app.services.project_service import ProjectService

router = APIRouter(tags=["resolutions"])


class ApprovalRequest(BaseModel):
    actor: str = "user"
    approver: Optional[str] = None


class RejectionRequest(BaseModel):
    actor: str = "user"
    reason: str = ""


# Support both /{project_id}/blockers/{blocker_id}/resolutions AND /{project_id}/blockers/{blocker_id}/propose-resolutions
@router.post("/{project_id}/blockers/{blocker_id}/resolutions", response_model=List[ResolutionProposal])
@router.post("/{project_id}/blockers/{blocker_id}/propose-resolutions", response_model=List[ResolutionProposal])
async def generate_resolutions(
    project_id: str,
    blocker_id: str,
    svc: ProjectService = Depends(get_project_service),
):
    project = svc.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
    blocker = svc.get_blocker(project_id, blocker_id)
    if not blocker:
        raise HTTPException(status_code=404, detail=f"Blocker '{blocker_id}' not found")
    return svc.generate_resolutions(project_id, blocker_id)


# Support both /{project_id}/resolutions AND /{project_id}/proposals
@router.get("/{project_id}/resolutions", response_model=List[ResolutionProposal])
@router.get("/{project_id}/proposals", response_model=List[ResolutionProposal])
async def list_resolutions(project_id: str, svc: ProjectService = Depends(get_project_service)):
    return svc.get_resolutions_for_project(project_id)


@router.get("/{project_id}/resolutions/{resolution_id}", response_model=ResolutionProposal)
@router.get("/{project_id}/proposals/{resolution_id}", response_model=ResolutionProposal)
async def get_resolution(
    project_id: str,
    resolution_id: str,
    svc: ProjectService = Depends(get_project_service),
):
    proposal = svc.get_resolution(resolution_id)
    if not proposal or proposal.project_id != project_id:
        raise HTTPException(status_code=404, detail=f"Resolution '{resolution_id}' not found")
    return proposal


@router.post("/{project_id}/resolutions/{resolution_id}/validate", response_model=ResolutionProposal)
@router.post("/{project_id}/proposals/{resolution_id}/validate", response_model=ResolutionProposal)
async def validate_resolution(
    project_id: str,
    resolution_id: str,
    svc: ProjectService = Depends(get_project_service),
):
    result = svc.validate_resolution(project_id, resolution_id)
    if not result:
        raise HTTPException(status_code=404, detail="Resolution or project not found")
    return result


@router.post("/{project_id}/resolutions/{resolution_id}/approve", response_model=ResolutionProposal)
@router.post("/{project_id}/proposals/{resolution_id}/approve", response_model=ResolutionProposal)
async def approve_resolution(
    project_id: str,
    resolution_id: str,
    body: ApprovalRequest = ApprovalRequest(),
    svc: ProjectService = Depends(get_project_service),
):
    actor = body.approver or body.actor
    try:
        result = svc.approve_resolution(project_id, resolution_id, actor=actor)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if not result:
        raise HTTPException(status_code=404, detail="Resolution or project not found")
    return result


@router.post("/{project_id}/resolutions/{resolution_id}/reject", response_model=ResolutionProposal)
@router.post("/{project_id}/proposals/{resolution_id}/reject", response_model=ResolutionProposal)
async def reject_resolution(
    project_id: str,
    resolution_id: str,
    body: RejectionRequest = RejectionRequest(),
    svc: ProjectService = Depends(get_project_service),
):
    result = svc.reject_resolution(project_id, resolution_id, actor=body.actor, reason=body.reason)
    if not result:
        raise HTTPException(status_code=404, detail="Resolution not found")
    return result
