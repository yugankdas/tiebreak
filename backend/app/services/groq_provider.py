"""Groq LLM Provider implementation for TIEBREAK.

Uses official Groq SDK.
Honors GROQ_API_KEY, GROQ_MODEL, GROQ_BASE_URL with graceful fallback and automatic dotenv loading.
"""
from __future__ import annotations
import json
import os
from pathlib import Path
import time
from typing import Any, Dict, List, Optional


def load_env_if_needed():
    """Load .env from project root or backend directory if not already populated."""
    for candidate in [
        Path.cwd() / ".env",
        Path.cwd().parent / ".env",
        Path(__file__).parent.parent.parent.parent / ".env",
    ]:
        if candidate.exists() and candidate.is_file():
            try:
                for line in candidate.read_text().splitlines():
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        k, v = line.split("=", 1)
                        k = k.strip()
                        v = v.strip()
                        if k not in os.environ and v:
                            os.environ[k] = v
            except Exception:
                pass


load_env_if_needed()


class GroqProvider:
    """Official Groq LLM Provider with connection testing and error categorization."""

    DEFAULT_MODEL = "openai/gpt-oss-120b"

    def __init__(self):
        load_env_if_needed()
        self.api_key = os.environ.get("GROQ_API_KEY") or os.environ.get("LLM_API_KEY", "")
        self.model = os.environ.get("GROQ_MODEL") or os.environ.get("LLM_MODEL", self.DEFAULT_MODEL)
        
        # In Groq official SDK, the client automatically appends /openai/v1 to requests.
        # If the environment variable GROQ_BASE_URL ends with /openai/v1 or contains api.groq.com,
        # pass "https://api.groq.com" explicitly so the SDK does not create /openai/v1/openai/v1.
        raw_base = os.environ.get("GROQ_BASE_URL") or os.environ.get("LLM_BASE_URL", "")
        if "api.groq.com" in raw_base:
            self.base_url = "https://api.groq.com"
        else:
            self.base_url = raw_base or "https://api.groq.com"

        self._client = None
        self._init_client()

    def _init_client(self):
        if self.api_key:
            try:
                from groq import Groq
                kwargs: Dict[str, Any] = {
                    "api_key": self.api_key,
                    "timeout": 45.0,
                    "max_retries": 2,
                }
                if self.base_url:
                    kwargs["base_url"] = self.base_url
                self._client = Groq(**kwargs)
            except Exception as e:
                print(f"[GroqProvider] Error initializing Groq client: {e}")
                self._client = None
        else:
            self._client = None

    @property
    def is_configured(self) -> bool:
        return bool(self.api_key and self.api_key.strip())

    def test_connection(self) -> Dict[str, Any]:
        """Performs a real, minimal chat completion request to verify connection."""
        if not self.is_configured:
            return {
                "configured": False,
                "connected": False,
                "provider": "groq",
                "model": self.model,
                "status": "NOT_CONFIGURED",
                "message": "GROQ_API_KEY is not configured. Running in deterministic demo mode.",
                "latency_ms": None,
            }

        start_time = time.time()
        try:
            if not self._client:
                self._init_client()

            if not self._client:
                return {
                    "configured": True,
                    "connected": False,
                    "provider": "groq",
                    "model": self.model,
                    "status": "CLIENT_INIT_FAILED",
                    "message": "Failed to initialize Groq client.",
                    "latency_ms": None,
                }

            # Real minimal chat completion request
            # Allocate sufficient tokens (150) for reasoning models (e.g. gpt-oss-120b)
            response = self._client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "user", "content": "Respond with only the word: PONG"}
                ],
                max_tokens=150,
                temperature=0.0,
            )
            latency_ms = int((time.time() - start_time) * 1000)
            model_returned = getattr(response, "model", self.model)
            
            return {
                "configured": True,
                "connected": True,
                "provider": "groq",
                "model": self.model,
                "actual_model": model_returned,
                "status": "CONNECTED",
                "message": f"Successfully connected to Groq API ({model_returned}) in {latency_ms}ms.",
                "latency_ms": latency_ms,
            }
        except Exception as e:
            latency_ms = int((time.time() - start_time) * 1000)
            err_str = str(e)
            
            # Safe categorization without exposing any keys
            if "authentication" in err_str.lower() or "401" in err_str or "invalid_api_key" in err_str.lower():
                err_category = "AUTHENTICATION_FAILED"
                msg = "Invalid Groq API key or unauthorized access."
            elif "model_not_found" in err_str.lower() or "404" in err_str:
                err_category = "MODEL_NOT_FOUND"
                msg = f"Configured model '{self.model}' is not available."
            elif "rate_limit" in err_str.lower() or "429" in err_str:
                err_category = "RATE_LIMITED"
                msg = "Groq rate limit exceeded. Please retry shortly."
            else:
                err_category = "CONNECTION_ERROR"
                msg = f"Failed to connect to Groq: {type(e).__name__}"

            return {
                "configured": True,
                "connected": False,
                "provider": "groq",
                "model": self.model,
                "status": err_category,
                "message": msg,
                "latency_ms": latency_ms,
            }

    def generate_json(self, prompt: str, system_prompt: Optional[str] = None) -> Optional[Dict[str, Any]]:
        """Sends structured chat completion request with JSON response format."""
        if not self.is_configured:
            return None

        try:
            if not self._client:
                self._init_client()
            if not self._client:
                return None

            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})

            # For reasoning models, allocate up to 4000 max_tokens
            response = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                response_format={"type": "json_object"},
                max_tokens=4000,
                temperature=0.2,
            )

            content = response.choices[0].message.content
            if not content:
                return None
            return json.loads(content)
        except Exception as e:
            print(f"[GroqProvider] Completion failed: {type(e).__name__} - {e}")
            return None
