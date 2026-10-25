"""Execution and verification endpoints with complete state return."""
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from typing import Any, Dict, List, Optional

from app.dependencies import get_project_service
from app.models.project import ExecutionResult, VerificationResult, Project, Blocker
from app.services.project_service import ProjectService

router = APIRouter(tags=["execution"])


class ExecutionResponse(BaseModel):
    execution: ExecutionResult
    verification: VerificationResult
    project: Project
    graph: Dict[str, Any]
    blockers: List[Blocker]


@router.post("/{project_id}/resolutions/{resolution_id}/execute", response_model=ExecutionResult)
@router.post("/{project_id}/proposals/{resolution_id}/execute", response_model=ExecutionResult)
async def execute_resolution(
    project_id: str,
    resolution_id: str,
    svc: ProjectService = Depends(get_project_service),
):
    proposal = svc.get_resolution(resolution_id)
    if not proposal or proposal.project_id != project_id:
        raise HTTPException(status_code=404, detail="Resolution not found")

    result = svc.execute_resolution(project_id, resolution_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Project or resolution not found")
    if not result.success:
        raise HTTPException(status_code=400, detail=result.error or "Execution failed")
    return result


@router.post("/{project_id}/resolutions/{resolution_id}/execute-and-verify", response_model=ExecutionResponse)
async def execute_and_verify_resolution(
    project_id: str,
    resolution_id: str,
    svc: ProjectService = Depends(get_project_service),
):
    """
    Executes an approved resolution, automatically triggers independent verification,
    and returns the updated authoritative project state, graph, and blockers in one call.
    """
    proposal = svc.get_resolution(resolution_id)
    if not proposal or proposal.project_id != project_id:
        raise HTTPException(status_code=404, detail="Resolution not found")

    exec_result = svc.execute_resolution(project_id, resolution_id)
    if exec_result is None:
        raise HTTPException(status_code=404, detail="Project or resolution not found")
    if not exec_result.success:
        raise HTTPException(status_code=400, detail=exec_result.error or "Execution failed")

    # Run verification immediately
    verif_result = svc.verify_resolution(project_id, resolution_id, proposal.blocker_id)
    if verif_result is None:
        raise HTTPException(status_code=500, detail="Outcome verification failed to compute")

    # Fetch updated state
    updated_project = svc.get_project(project_id)
    updated_graph = svc.get_graph(project_id) or {"nodes": [], "edges": [], "cycles": []}
    updated_blockers = svc.get_blockers(project_id)

    return ExecutionResponse(
        execution=exec_result,
        verification=verif_result,
        project=updated_project,
        graph=updated_graph,
        blockers=updated_blockers,
    )


@router.post("/{project_id}/resolutions/{resolution_id}/verify")
@router.post("/{project_id}/proposals/{resolution_id}/verify")
async def verify_resolution(
    project_id: str,
    resolution_id: str,
    blocker_id: Optional[str] = Query(None),
    svc: ProjectService = Depends(get_project_service),
) -> VerificationResult:
    proposal = svc.get_resolution(resolution_id)
    if not proposal or proposal.project_id != project_id:
        raise HTTPException(status_code=404, detail="Resolution not found")

    target_blocker = blocker_id or proposal.blocker_id
    result = svc.verify_resolution(project_id, resolution_id, target_blocker)
    if result is None:
        raise HTTPException(status_code=404, detail="Project, resolution, or blocker not found")
    return result


@router.get("/{project_id}/verify")
@router.post("/{project_id}/verify")
async def verify_project(
    project_id: str,
    svc: ProjectService = Depends(get_project_service),
) -> Dict[str, Any]:
    """Verify general project health, remaining blockers, and resolution status."""
    project = svc.get_project(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    blockers = svc.get_blockers(project_id)
    return {
        "verified_at": "now",
        "is_resolved": len(blockers) == 0,
        "resolved_blocker_id": "",
        "remaining_blockers": len(blockers),
        "new_blockers_introduced": 0,
        "details": f"Project has {len(blockers)} active blockers remaining.",
    }


@router.get("/{project_id}/resolutions/{resolution_id}/execution-result")
@router.get("/{project_id}/proposals/{resolution_id}/execution-result")
async def get_execution_result(
    project_id: str,
    resolution_id: str,
    svc: ProjectService = Depends(get_project_service),
) -> Optional[ExecutionResult]:
    return svc.get_execution_result(resolution_id)


@router.get("/{project_id}/resolutions/{resolution_id}/verification-result")
@router.get("/{project_id}/proposals/{resolution_id}/verification-result")
async def get_verification_result(
    project_id: str,
    resolution_id: str,
    svc: ProjectService = Depends(get_project_service),
) -> Optional[VerificationResult]:
    return svc.get_verification_result(resolution_id)
