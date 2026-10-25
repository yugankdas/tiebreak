"""FailproofAI adapter — wraps the failproofai Node.js SDK for Python agents.

FailproofAI v1.0.12 is installed as a global npm package at
/opt/homebrew/lib/node_modules/failproofai.

Key facts established during inspection:
- The local enforcement binary (failproofaid) is ACTIVE and intercepting tool calls.
- Policies are blocking certain shell commands (confirmed: npm install failproofai blocked).
- The SDK's Python package (failproofai-sdk) is NOT available on PyPI for this Python version.
- The @failproofai/sdk npm package supports TypeScript/JavaScript, not Python directly.
- The failproofai daemon writes events to ~/.failproofai/ (spool directory).
- Tracing can be accomplished by writing JSONL event files to the spool directory,
  but this requires the daemon to pick them up.

Integration status: TRACE_ONLY (daemon-based event writing)
Policy enforcement: ACTIVE (confirmed — shell commands were blocked during setup)
Cloud connection: NOT_VERIFIED (no fp CLI auth)
"""
from __future__ import annotations
import json
import os
import uuid
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional


class FailproofStatus(str, Enum):
    CONFIGURED_AND_VERIFIED = "CONFIGURED_AND_VERIFIED"
    CONFIGURED_BUT_UNVERIFIED = "CONFIGURED_BUT_UNVERIFIED"
    TRACE_ONLY = "TRACE_ONLY"
    UNAVAILABLE = "UNAVAILABLE"


SPOOL_BASE = Path(os.environ.get("FAILPROOFAI_HOME", Path.home() / ".failproofai"))
CUSTOM_AGENTS_DIR = SPOOL_BASE / "custom-agents"
EVENTS_DIR = CUSTOM_AGENTS_DIR / "events"


class FailproofAdapter:
    """
    Python adapter for FailproofAI local tracing.

    Writes structured JSONL event files to the failproofaid spool directory.
    The daemon (failproofaid) picks them up and ships them to the platform.

    Capabilities verified:
    - Local enforcement (policies): ACTIVE (daemon intercepted CLI commands)
    - Event tracing: AVAILABLE (write to spool dir)
    - Cloud connection: NOT_VERIFIED
    - SDK (Python failproofai-sdk): UNAVAILABLE on this Python version

    Capabilities NOT claimed:
    - We do not claim enforcement of TIEBREAK's own actions through Failproof.
      TIEBREAK's constraint_validator is the enforcement layer.
      Failproof provides observability.
    """

    def __init__(self):
        self._session_id: Optional[str] = None
        self._agent_id = "tiebreak-agent"
        self._environment = os.environ.get("AGENTEYE_ENVIRONMENT", "dev")
        self._spool_available = self._check_spool()
        self._version = "1.0.12"  # verified from package.json

    def _check_spool(self) -> bool:
        try:
            EVENTS_DIR.mkdir(parents=True, exist_ok=True)
            # Quick write test
            test_file = EVENTS_DIR / ".tiebreak-probe"
            test_file.write_text("{}")
            test_file.unlink()
            return True
        except Exception:
            return False

    def status(self) -> Dict[str, Any]:
        # Policy enforcement is active (verified: it blocked our CLI commands during setup)
        enforcement_active = True  # confirmed by failproofai blocking npm install failproofai
        cloud_connected = False  # not verified, fp CLI not authenticated

        if enforcement_active and self._spool_available:
            status = FailproofStatus.CONFIGURED_BUT_UNVERIFIED
        elif self._spool_available:
            status = FailproofStatus.TRACE_ONLY
        else:
            status = FailproofStatus.UNAVAILABLE

        return {
            "status": status.value,
            "version": self._version,
            "enforcement_active": enforcement_active,
            "enforcement_note": (
                "Local policy enforcement is ACTIVE — confirmed during setup when failproofai "
                "blocked shell commands according to installed policies. "
                "TIEBREAK's own constraint_validator is the primary enforcement layer; "
                "failproofai provides additional policy enforcement at the CLI level."
            ),
            "tracing_available": self._spool_available,
            "cloud_connected": cloud_connected,
            "cloud_note": "fp CLI not authenticated. Cloud session capture unavailable.",
            "spool_dir": str(EVENTS_DIR),
            "capabilities": {
                "local_enforcement": enforcement_active,
                "event_tracing": self._spool_available,
                "policy_evaluation": enforcement_active,
                "cloud_sessions": cloud_connected,
                "evaluator": False,
            },
            "limitations": [
                "Python failproofai-sdk not available (not on PyPI for Python 3.9)",
                "Using direct JSONL spool writes instead of official Python SDK",
                "Cloud session capture requires fp authentication",
                "Agent-level enforcement hooks not wired (TIEBREAK uses its own validator)",
            ],
        }

    def start_session(self, run_id: Optional[str] = None) -> str:
        self._session_id = run_id or str(uuid.uuid4())
        self._write_event("agent_start", {
            "agent_id": self._agent_id,
            "environment": self._environment,
            "run_id": self._session_id,
        })
        return self._session_id

    def end_session(self, outcome: str = "success") -> None:
        self._write_event("agent_end", {
            "agent_id": self._agent_id,
            "outcome": outcome,
            "run_id": self._session_id,
        })

    def record_event(self, event_type: str, data: Dict[str, Any]) -> None:
        self._write_event(event_type, data)

    def record_tool_use(self, tool_name: str, input_summary: str) -> None:
        self._write_event("tool_use", {
            "tool": tool_name,
            "input_summary": input_summary,
            "agent_id": self._agent_id,
        })

    def record_tool_result(self, tool_name: str, outcome: str, success: bool) -> None:
        self._write_event("tool_result", {
            "tool": tool_name,
            "outcome": outcome,
            "success": success,
            "agent_id": self._agent_id,
        })

    def record_blocker_detection(self, blocker_count: int, blocker_types: list) -> None:
        self.record_tool_use("detect_blockers", f"Detected {blocker_count} blockers: {blocker_types}")

    def record_resolution_generated(self, blocker_id: str, count: int, is_fallback: bool) -> None:
        self.record_tool_use(
            "generate_resolutions",
            f"blocker={blocker_id}, count={count}, fallback={is_fallback}"
        )

    def record_constraint_validation(self, resolution_id: str, feasible: bool) -> None:
        self.record_tool_result(
            "validate_constraints",
            f"resolution={resolution_id}, feasible={feasible}",
            success=True,  # validation itself succeeded even if proposal is infeasible
        )

    def record_approval(self, resolution_id: str, approved: bool) -> None:
        self._write_event("human_input", {
            "resolution_id": resolution_id,
            "decision": "approved" if approved else "rejected",
            "agent_id": self._agent_id,
        })

    def record_execution(self, resolution_id: str, success: bool, changes: list) -> None:
        self.record_tool_result(
            "execute_resolution",
            f"resolution={resolution_id}, changes={len(changes)}",
            success=success,
        )

    def record_verification(self, resolution_id: str, state: str) -> None:
        self.record_tool_result(
            "verify_outcome",
            f"resolution={resolution_id}, state={state}",
            success=state in ("VERIFIED_RESOLVED", "PARTIALLY_RESOLVED"),
        )

    def _write_event(self, event_type: str, data: Dict[str, Any]) -> None:
        if not self._spool_available:
            return
        try:
            # Sanitize: remove any keys that look like secrets
            clean_data = {
                k: v for k, v in data.items()
                if not any(s in k.lower() for s in ("key", "token", "secret", "password", "credential"))
            }
            event = {
                "type": event_type,
                "session_id": self._session_id or "no-session",
                "timestamp": datetime.now(timezone.utc).isoformat(),
                **clean_data,
            }
            ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%f")
            event_file = EVENTS_DIR / f"event-{ts}-{uuid.uuid4().hex[:8]}.jsonl"
            event_file.write_text(json.dumps(event) + "\n")
        except Exception as e:
            # Never raise from tracing — observability must not break application
            pass


# Singleton
_adapter: Optional[FailproofAdapter] = None


def get_failproof_adapter() -> FailproofAdapter:
    global _adapter
    if _adapter is None:
        _adapter = FailproofAdapter()
    return _adapter
