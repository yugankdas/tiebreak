"""Project endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from typing import List

from app.dependencies import get_project_service
from app.models.project import Project
from app.services.project_service import ProjectService

router = APIRouter(tags=["projects"])


@router.get("", response_model=List[Project])
async def list_projects(svc: ProjectService = Depends(get_project_service)):
    return svc.list_projects()


@router.get("/{project_id}", response_model=Project)
async def get_project(project_id: str, svc: ProjectService = Depends(get_project_service)):
    project = svc.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
    return project


@router.post("/{project_id}/reset", response_model=Project)
async def reset_project(project_id: str, svc: ProjectService = Depends(get_project_service)):
    project = svc.reset_demo(project_id)
    if not project:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found or reset failed")
    return project
