"""Integrations endpoints for Groq and FailproofAI."""
from fastapi import APIRouter, Depends
from typing import Any, Dict

from app.services.failproof_adapter import get_failproof_adapter, FailproofAdapter
from app.services.groq_provider import GroqProvider

router = APIRouter(tags=["integrations"])


def get_groq_provider() -> GroqProvider:
    return GroqProvider()


@router.get("/failproof/status")
async def failproof_status(adapter: FailproofAdapter = Depends(get_failproof_adapter)) -> Dict[str, Any]:
    return adapter.status()


@router.get("/groq/status")
async def groq_status(provider: GroqProvider = Depends(get_groq_provider)) -> Dict[str, Any]:
    """Tests the real Groq connection with a minimal request, returning sanitized status."""
    return provider.test_connection()


@router.get("/status")
async def integrations_status(
    groq: GroqProvider = Depends(get_groq_provider),
    failproof: FailproofAdapter = Depends(get_failproof_adapter),
) -> Dict[str, Any]:
    """Combined integration status for UI header/dashboard."""
    return {
        "groq": groq.test_connection(),
        "failproof": failproof.status(),
    }
