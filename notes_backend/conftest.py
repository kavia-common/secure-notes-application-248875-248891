"""
Pytest fixtures for notes_backend integration tests.

Why this file exists:
- Pytest only auto-loads fixtures from files named `conftest.py` (in the test folder tree).
- The generated tests expect a `client` fixture (httpx.AsyncClient) already available.

Important:
- The production app reads settings at import time (src.api.config.get_settings()).
  Therefore, required env vars must be set BEFORE importing src.api.main.
"""

from __future__ import annotations

import os
from collections.abc import AsyncIterator
from typing import Any, Dict

import pytest
from httpx import ASGITransport, AsyncClient


@pytest.fixture(scope="session", autouse=True)
def _set_required_env() -> None:
    """
    Ensure required settings env vars exist for tests.

    The app requires:
    POSTGRES_URL, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, POSTGRES_PORT, JWT_SECRET_KEY

    In CI or other environments, these may already be set; we do not override
    existing values.
    """
    defaults: Dict[str, str] = {
        # DB defaults (only used if orchestrator/CI didn't provide them)
        "POSTGRES_URL": "postgresql://localhost:5000/myapp",
        "POSTGRES_USER": "appuser",
        "POSTGRES_PASSWORD": "dbuser123",
        "POSTGRES_DB": "myapp",
        "POSTGRES_PORT": "5000",
        # JWT for tests
        "JWT_SECRET_KEY": "test_jwt_secret_key_change_me",
        "JWT_ALGORITHM": "HS256",
        "JWT_ACCESS_TOKEN_EXP_MINUTES": "60",
        # Optional settings
        "CORS_ALLOW_ORIGINS": "http://localhost:3000",
        "ENVIRONMENT": "test",
        "APP_NAME": "Secure Notes API (test)",
    }

    for k, v in defaults.items():
        os.environ.setdefault(k, v)


@pytest.fixture(scope="session")
def app() -> Any:
    """
    Import and return the FastAPI app.

    Uses a late import so the env var fixture runs first.
    """
    # Late import so env fixture runs first.
    from src.api.main import app as fastapi_app  # noqa: WPS433 (import inside function)

    return fastapi_app


@pytest.fixture()
async def client(app: Any) -> AsyncIterator[AsyncClient]:
    """Create an AsyncClient wired to the FastAPI ASGI app."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac


async def _signup_and_get_token(ac: AsyncClient, *, email: str, password: str) -> str:
    """Helper to create a user and return a JWT access token."""
    resp = await ac.post("/auth/signup", json={"email": email, "password": password})
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert "access_token" in data
    return data["access_token"]


@pytest.fixture()
async def auth_headers(client: AsyncClient) -> Dict[str, str]:
    """Create a user and return Authorization headers."""
    token = await _signup_and_get_token(
        client,
        email="user1@example.com",
        password="password123",
    )
    return {"Authorization": f"Bearer {token}"}
