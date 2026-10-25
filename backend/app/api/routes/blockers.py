"""Blocker endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from typing import List

from app.dependencies import get_project_service
from app.models.project import Blocker
from app.services.project_service import ProjectService

router = APIRouter(tags=["blockers"])


@router.post("/{project_id}/detect-blockers", response_model=List[Blocker])
async def detect_blockers(project_id: str, svc: ProjectService = Depends(get_project_service)):
    project = svc.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
    return svc.detect_blockers(project_id)


@router.get("/{project_id}/blockers", response_model=List[Blocker])
async def get_blockers(project_id: str, svc: ProjectService = Depends(get_project_service)):
    project = svc.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
    return svc.get_blockers(project_id)


@router.get("/{project_id}/blockers/{blocker_id}", response_model=Blocker)
async def get_blocker(project_id: str, blocker_id: str, svc: ProjectService = Depends(get_project_service)):
    blocker = svc.get_blocker(project_id, blocker_id)
    if not blocker:
        raise HTTPException(status_code=404, detail=f"Blocker '{blocker_id}' not found")
    return blocker
