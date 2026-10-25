"""Audit trail endpoint."""
from fastapi import APIRouter, Depends, HTTPException
from typing import List

from app.dependencies import get_project_service
from app.models.project import AuditEvent
from app.services.project_service import ProjectService

router = APIRouter(tags=["audit"])


@router.get("/{project_id}/audit", response_model=List[AuditEvent])
async def get_audit(project_id: str, svc: ProjectService = Depends(get_project_service)):
    project = svc.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
    return svc.audit.get_for_project(project_id)
