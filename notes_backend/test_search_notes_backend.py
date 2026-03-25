from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_search_notes_matches_title_and_content(client: AsyncClient, auth_headers: dict) -> None:
    await client.post(
        "/notes",
        headers=auth_headers,
        json={"title": "Shopping list", "content": "Buy milk and eggs", "content_markdown": "", "tags": []},
    )
    await client.post(
        "/notes",
        headers=auth_headers,
        json={"title": "Work plan", "content": "Finish quarterly report", "content_markdown": "", "tags": []},
    )

    # Search by title keyword
    resp1 = await client.get("/notes/search?q=shopping", headers=auth_headers)
    assert resp1.status_code == 200, resp1.text
    data1 = resp1.json()
    assert data1["total"] >= 1
    assert any("Shopping list" == item["title"] for item in data1["items"])

    # Search by content keyword
    resp2 = await client.get("/notes/search?q=quarterly", headers=auth_headers)
    assert resp2.status_code == 200, resp2.text
    data2 = resp2.json()
    assert data2["total"] >= 1
    assert any("Work plan" == item["title"] for item in data2["items"])

    # Empty query should be rejected by validation (min_length=1)
    resp3 = await client.get("/notes/search?q=", headers=auth_headers)
    assert resp3.status_code in (422, 400)
