"""
tests/conftest.py
------------------
Shared pytest fixtures for the FacebookReplay test suite.

All external dependencies (database, HuggingFace, Facebook API) are
mocked/stubbed so the test suite runs offline without Docker or
any live services.
"""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient


# ── Patch environment BEFORE any app import ────────────────────────────────
# Secrets require env vars; set minimal fakes before the module loads.
import os

os.environ.setdefault("HF_TOKEN", "hf_test_token")
os.environ.setdefault("FB_TOKEN", "fb_test_token")
os.environ.setdefault("FB_VERIFY_TOKEN", "fb_verify_test")
os.environ.setdefault(
    "DATABASE_URL",
    "postgresql+asyncpg://test:test@localhost:5432/test_db",
)


# ── FastAPI TestClient ─────────────────────────────────────────────────────

@pytest.fixture()
def app():
    """Import the FastAPI application (no lifespan — DB init is skipped)."""
    from main import app as _app
    return _app


@pytest.fixture()
async def client(app):
    """Async HTTP test client wired to the FastAPI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ── Reusable mock factories ───────────────────────────────────────────────

@pytest.fixture()
def mock_hf_client():
    """Patch HFClient.generate to return a canned LLM response."""
    mock = AsyncMock(return_value="Mocked LLM response")
    with patch("app.infrastructure.hf_client.hf_client.generate", mock):
        yield mock


@pytest.fixture()
def mock_facebook_client():
    """Patch both Facebook API methods with no-op async stubs."""
    post_reply = AsyncMock(return_value={"id": "mock_reply_id"})
    send_dm    = AsyncMock(return_value={"recipient_id": "r", "message_id": "m"})
    with patch(
        "app.infrastructure.facebook_client.facebook_client.post_reply",
        post_reply,
    ), patch(
        "app.infrastructure.facebook_client.facebook_client.send_messenger_message",
        send_dm,
    ):
        yield {"post_reply": post_reply, "send_messenger_message": send_dm}
