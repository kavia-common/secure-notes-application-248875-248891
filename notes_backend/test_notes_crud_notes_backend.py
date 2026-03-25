from __future__ import annotations

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_create_get_update_delete_note_happy_path(client: AsyncClient, auth_headers: dict) -> None:
    # Create
    create = await client.post(
        "/notes",
        headers=auth_headers,
        json={
            "title": "First",
            "content": "hello world",
            "content_markdown": "# hello world",
            "tags": ["Work", "urgent"],
        },
    )
    assert create.status_code == 201, create.text
    note = create.json()
    note_id = note["id"]
    assert note["title"] == "First"
    assert sorted(note["tags"], key=str.lower) == ["urgent", "Work"]

    # Get
    get_resp = await client.get(f"/notes/{note_id}", headers=auth_headers)
    assert get_resp.status_code == 200, get_resp.text
    fetched = get_resp.json()
    assert fetched["id"] == note_id
    assert fetched["content"] == "hello world"

    # Update: change title + replace tags
    upd = await client.put(
        f"/notes/{note_id}",
        headers=auth_headers,
        json={"title": "Updated", "tags": ["Personal"]},
    )
    assert upd.status_code == 200, upd.text
    updated = upd.json()
    assert updated["title"] == "Updated"
    assert updated["tags"] == ["Personal"]

    # Archive it
    arch = await client.put(
        f"/notes/{note_id}",
        headers=auth_headers,
        json={"archived": True},
    )
    assert arch.status_code == 200, arch.text
    assert arch.json()["archived_at"] is not None

    # Delete
    del_resp = await client.delete(f"/notes/{note_id}", headers=auth_headers)
    assert del_resp.status_code == 204, del_resp.text

    # Get after delete => 404
    get_after = await client.get(f"/notes/{note_id}", headers=auth_headers)
    assert get_after.status_code == 404, get_after.text
    assert get_after.json()["detail"] == "Note not found"


@pytest.mark.asyncio
async def test_list_notes_pagination_and_filters(client: AsyncClient, auth_headers: dict) -> None:
    # Create three notes with different tags/archived
    n1 = await client.post(
        "/notes",
        headers=auth_headers,
        json={"title": "A", "content": "alpha", "content_markdown": "", "tags": ["t1"]},
    )
    n2 = await client.post(
        "/notes",
        headers=auth_headers,
        json={"title": "B", "content": "beta", "content_markdown": "", "tags": ["t2"]},
    )
    n3 = await client.post(
        "/notes",
        headers=auth_headers,
        json={"title": "C", "content": "gamma", "content_markdown": "", "tags": ["t1", "t2"]},
    )
    assert n1.status_code == 201 and n2.status_code == 201 and n3.status_code == 201

    # Archive note B
    note_b_id = n2.json()["id"]
    arch = await client.put(f"/notes/{note_b_id}", headers=auth_headers, json={"archived": True})
    assert arch.status_code == 200, arch.text

    # List all
    all_notes = await client.get("/notes?offset=0&limit=50", headers=auth_headers)
    assert all_notes.status_code == 200, all_notes.text
    all_data = all_notes.json()
    assert all_data["total"] >= 3
    assert len(all_data["items"]) >= 3

    # Filter by tag t1
    t1 = await client.get("/notes?tag=t1", headers=auth_headers)
    assert t1.status_code == 200, t1.text
    t1_items = t1.json()["items"]
    assert len(t1_items) >= 2
    assert all("t1" in item["tags"] for item in t1_items)

    # Filter archived only
    archived_only = await client.get("/notes?archived=true", headers=auth_headers)
    assert archived_only.status_code == 200, archived_only.text
    arch_items = archived_only.json()["items"]
    assert any(item["id"] == note_b_id for item in arch_items)
    assert all(item["archived_at"] is not None for item in arch_items)

    # Filter unarchived only
    unarchived_only = await client.get("/notes?archived=false", headers=auth_headers)
    assert unarchived_only.status_code == 200, unarchived_only.text
    unarch_items = unarchived_only.json()["items"]
    assert all(item["archived_at"] is None for item in unarch_items)
