"""Graph endpoints."""
from fastapi import APIRouter, Depends, HTTPException
from typing import Any, Dict

from app.dependencies import get_project_service
from app.services.project_service import ProjectService

router = APIRouter(tags=["graph"])


@router.get("/{project_id}/graph")
async def get_graph(project_id: str, svc: ProjectService = Depends(get_project_service)) -> Dict[str, Any]:
    graph = svc.get_graph(project_id)
    if graph is None:
        raise HTTPException(status_code=404, detail=f"Project '{project_id}' not found")
    return graph
