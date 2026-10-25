"""FastAPI main application."""
from __future__ import annotations
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.routes import (
    health, projects, graph, blockers, resolutions, execution, audit, integrations, approvals
)


def create_app() -> FastAPI:
    app = FastAPI(
        title="TIEBREAK API",
        description="AI-powered project deadlock resolution agent",
        version="1.0.0",
    )

    # CORS — allow frontend dev server and production
    origins = os.environ.get("CORS_ORIGINS", "http://localhost:5173,http://localhost:3000").split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routes
    app.include_router(health.router, prefix="/api")
    app.include_router(projects.router, prefix="/api/projects")
    app.include_router(graph.router, prefix="/api/projects")
    app.include_router(blockers.router, prefix="/api/projects")
    app.include_router(resolutions.router, prefix="/api/projects")
    app.include_router(execution.router, prefix="/api/projects")
    app.include_router(audit.router, prefix="/api/projects")
    app.include_router(integrations.router, prefix="/api/integrations")
    app.include_router(approvals.router, prefix="/api/organization")

    return app


app = create_app()
