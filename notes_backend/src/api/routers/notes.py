import uuid
from typing import Annotated, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.auth import get_current_user
from src.api.db import get_db_session
from src.api.models import NoteTag, User
from src.api.schemas import NoteCreateRequest, NoteListResponse, NoteResponse, NoteUpdateRequest, SearchResponse
from src.api.services import create_note, delete_note, get_note, list_notes, search_notes, update_note

router = APIRouter(prefix="/notes", tags=["notes"])


def _to_note_response(note) -> NoteResponse:
    return NoteResponse(
        id=note.id,
        title=note.title,
        content=note.content,
        content_markdown=note.content_markdown,
        created_at=note.created_at,
        updated_at=note.updated_at,
        archived_at=note.archived_at,
        tags=sorted([nt.tag.name for nt in note.note_tags if isinstance(nt, NoteTag) and nt.tag], key=lambda s: s.lower()),
    )


@router.post(
    "",
    response_model=NoteResponse,
    summary="Create note",
    description="Create a note for the authenticated user.",
    status_code=status.HTTP_201_CREATED,
)
async def create_note_endpoint(
    payload: NoteCreateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> NoteResponse:
    """Create a note and optionally attach tags by name."""
    note = await create_note(
        session,
        user=current_user,
        title=payload.title,
        content=payload.content,
        content_markdown=payload.content_markdown,
        tags=payload.tags,
    )
    await session.commit()
    return _to_note_response(note)


@router.get(
    "",
    response_model=NoteListResponse,
    summary="List notes",
    description="List notes belonging to the authenticated user, optionally filtered by tag and archived state.",
)
async def list_notes_endpoint(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
    offset: int = Query(0, ge=0, description="Pagination offset."),
    limit: int = Query(50, ge=1, le=200, description="Pagination limit."),
    tag: Optional[str] = Query(None, description="Filter by tag name."),
    archived: Optional[bool] = Query(None, description="If true list archived only; if false list unarchived only."),
) -> NoteListResponse:
    """List notes for the current user."""
    notes, total = await list_notes(session, user=current_user, offset=offset, limit=limit, tag=tag, archived=archived)
    return NoteListResponse(items=[_to_note_response(n) for n in notes], total=total, offset=offset, limit=limit)


@router.get(
    "/{note_id}",
    response_model=NoteResponse,
    summary="Get note",
    description="Get a single note by id (must belong to authenticated user).",
)
async def get_note_endpoint(
    note_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> NoteResponse:
    """Fetch a note by id."""
    note = await get_note(session, user=current_user, note_id=note_id)
    return _to_note_response(note)


@router.put(
    "/{note_id}",
    response_model=NoteResponse,
    summary="Update note",
    description="Update a note (fields and/or tags). Note must belong to authenticated user.",
)
async def update_note_endpoint(
    note_id: uuid.UUID,
    payload: NoteUpdateRequest,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> NoteResponse:
    """Update a note."""
    note = await update_note(
        session,
        user=current_user,
        note_id=note_id,
        title=payload.title,
        content=payload.content,
        content_markdown=payload.content_markdown,
        archived=payload.archived,
        tags=payload.tags,
    )
    await session.commit()
    return _to_note_response(note)


@router.delete(
    "/{note_id}",
    summary="Delete note",
    description="Delete a note by id (must belong to authenticated user).",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_note_endpoint(
    note_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> None:
    """Delete a note."""
    await delete_note(session, user=current_user, note_id=note_id)
    await session.commit()
    return None


@router.get(
    "/search",
    response_model=SearchResponse,
    summary="Search notes",
    description="Search notes (full-text + fuzzy) scoped to authenticated user.",
)
async def search_notes_endpoint(
    q: str = Query(..., min_length=1, description="Search query string."),
    offset: int = Query(0, ge=0, description="Pagination offset."),
    limit: int = Query(50, ge=1, le=200, description="Pagination limit."),
    current_user: Annotated[User, Depends(get_current_user)] = None,
    session: Annotated[AsyncSession, Depends(get_db_session)] = None,
) -> SearchResponse:
    """Search notes for a user."""
    notes, total = await search_notes(session, user=current_user, query=q, offset=offset, limit=limit)
    return SearchResponse(items=[_to_note_response(n) for n in notes], total=total, offset=offset, limit=limit)
