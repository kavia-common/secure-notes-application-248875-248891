from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_list_tags_and_delete_tag(client: AsyncClient, auth_headers: dict) -> None:
    # Create note with tags to create tag rows
    note = await client.post(
        "/notes",
        headers=auth_headers,
        json={"title": "Tagged", "content": "", "content_markdown": "", "tags": ["alpha", "beta"]},
    )
    assert note.status_code == 201, note.text

    # List tags
    tags_resp = await client.get("/tags", headers=auth_headers)
    assert tags_resp.status_code == 200, tags_resp.text
    tags = tags_resp.json()["items"]
    names = [t["name"] for t in tags]
    assert "alpha" in names and "beta" in names

    # Delete one tag
    alpha_tag = next(t for t in tags if t["name"] == "alpha")
    del_resp = await client.delete(f"/tags/{alpha_tag['id']}", headers=auth_headers)
    assert del_resp.status_code == 204, del_resp.text

    # Tag should be gone
    tags_resp2 = await client.get("/tags", headers=auth_headers)
    assert tags_resp2.status_code == 200
    names2 = [t["name"] for t in tags_resp2.json()["items"]]
    assert "alpha" not in names2
