from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_signup_returns_token(client: AsyncClient) -> None:
    resp = await client.post(
        "/auth/signup",
        json={"email": "newuser@example.com", "password": "password123"},
    )
    assert resp.status_code == 201, resp.text
    data = resp.json()
    assert data["token_type"] == "bearer"
    assert isinstance(data["access_token"], str)
    assert data["access_token"]


@pytest.mark.asyncio
async def test_signup_duplicate_email_returns_409(client: AsyncClient) -> None:
    payload = {"email": "dup@example.com", "password": "password123"}
    r1 = await client.post("/auth/signup", json=payload)
    assert r1.status_code == 201, r1.text

    r2 = await client.post("/auth/signup", json=payload)
    assert r2.status_code == 409, r2.text
    assert r2.json()["detail"] == "Email already registered"


@pytest.mark.asyncio
async def test_login_with_wrong_password_returns_401(client: AsyncClient) -> None:
    await client.post("/auth/signup", json={"email": "login1@example.com", "password": "password123"})

    resp = await client.post("/auth/login", json={"email": "login1@example.com", "password": "wrongpass"})
    assert resp.status_code == 401, resp.text
    assert resp.json()["detail"] == "Invalid email or password"


@pytest.mark.asyncio
async def test_me_requires_auth(client: AsyncClient) -> None:
    resp = await client.get("/auth/me")
    assert resp.status_code == 401, resp.text


@pytest.mark.asyncio
async def test_me_returns_current_user(client: AsyncClient) -> None:
    signup = await client.post(
        "/auth/signup",
        json={"email": "me@example.com", "password": "password123"},
    )
    token = signup.json()["access_token"]

    resp = await client.get("/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["email"] == "me@example.com"
    assert "id" in data
