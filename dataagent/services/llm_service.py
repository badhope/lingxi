"""LLM service.

Single place to talk to the chat model. Wraps `config.settings` and
`langchain_openai.ChatOpenAI`. Routers and other services import
`call_llm` / `call_llm_json` / `get_llm_client` from here.
"""
from __future__ import annotations

import json
import asyncio
from typing import Any, Dict, List, Optional

from config import settings

try:
    from langchain_openai import ChatOpenAI
    from langchain_core.messages import HumanMessage, SystemMessage
    _HAS_LC = True
except ImportError:  # pragma: no cover
    _HAS_LC = False


_client: Optional["ChatOpenAI"] = None


def get_llm_client() -> "ChatOpenAI":
    """Return a process-wide ChatOpenAI client."""
    global _client
    if not _HAS_LC:  # pragma: no cover
        raise RuntimeError("langchain_openai is not installed")
    if _client is None:
        _client = ChatOpenAI(
            model=settings.default_model,
            temperature=settings.default_temperature,
            api_key=settings.openai_api_key or "dummy-key",
            base_url=settings.openai_base_url,
        )
    return _client


async def call_llm(prompt: str, _settings=None) -> str:
    """Send a single prompt, return the text response."""
    client = get_llm_client()
    msg = await client.ainvoke([HumanMessage(content=prompt)])
    return getattr(msg, "content", "") or ""


async def call_llm_json(prompt: str, _settings=None) -> Dict[str, Any]:
    """Send a prompt, expect JSON, return parsed dict (or {"raw": ...})."""
    text = await call_llm(prompt, _settings)
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return {"raw": text}


async def test_connection(_config: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Smoke-test that the configured provider responds."""
    try:
        text = await call_llm("ping", _config)
        return {"ok": bool(text), "sample": text[:120]}
    except Exception as exc:  # pragma: no cover
        return {"ok": False, "error": str(exc)}


async def verify_model_exists(_model: str) -> bool:  # pragma: no cover
    """Best-effort check; we only have one configured model today."""
    return bool(settings.default_model)


async def list_available_models() -> List[str]:  # pragma: no cover
    return [settings.default_model]


async def get_account_info() -> Dict[str, Any]:  # pragma: no cover
    return {"provider": "openai-compatible", "base_url": settings.openai_base_url}


__all__ = [
    "get_llm_client",
    "call_llm",
    "call_llm_json",
    "test_connection",
    "verify_model_exists",
    "list_available_models",
    "get_account_info",
]
