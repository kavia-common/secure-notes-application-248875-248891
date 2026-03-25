import uuid
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from fastapi import HTTPException, status
from sqlalchemy import and_, delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from src.api.models import Note, NoteTag, Tag, User


async def _get_or_create_tags(
    session: AsyncSession, *, user_id: uuid.UUID, tag_names: List[str]
) -> List[Tag]:
    normalized = []
    for name in tag_names:
        trimmed = name.strip()
        if trimmed:
            normalized.append(trimmed)
    # Deduplicate case-insensitively while preserving user intent-ish order.
    seen = set()
    deduped: List[str] = []
    for n in normalized:
        key = n.lower()
        if key not in seen:
            seen.add(key)
            deduped.append(n)

    if not deduped:
        return []

    # Fetch existing tags for user.
    res = await session.execute(
        select(Tag).where(and_(Tag.user_id == user_id, func.lower(Tag.name).in_([n.lower() for n in deduped])))
    )
    existing = res.scalars().all()
    existing_by_lower = {t.name.lower(): t for t in existing}

    to_create = [n for n in deduped if n.lower() not in existing_by_lower]
    created: List[Tag] = []
    for name in to_create:
        tag = Tag(user_id=user_id, name=name)
        session.add(tag)
        created.append(tag)

    await session.flush()  # assign ids for created tags
    return existing + created


def _note_to_tag_names(note: Note) -> List[str]:
    return sorted([nt.tag.name for nt in note.note_tags if nt.tag is not None], key=lambda s: s.lower())


async def _get_note_or_404(session: AsyncSession, *, user_id: uuid.UUID, note_id: uuid.UUID) -> Note:
    res = await session.execute(
        select(Note)
        .where(and_(Note.id == note_id, Note.user_id == user_id))
        .options(selectinload(Note.note_tags).selectinload(NoteTag.tag))
    )
    note = res.scalar_one_or_none()
    if not note:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Note not found")
    return note


# PUBLIC_INTERFACE
async def create_note(
    session: AsyncSession, *, user: User, title: str, content: str, content_markdown: str, tags: List[str]
) -> Note:
    """PUBLIC_INTERFACE: Create a new note for a user with optional tags."""
    note = Note(user_id=user.id, title=title or "", content=content or "", content_markdown=content_markdown or "")
    session.add(note)
    await session.flush()

    tag_objs = await _get_or_create_tags(session, user_id=user.id, tag_names=tags)
    for tag in tag_objs:
        session.add(NoteTag(note_id=note.id, tag_id=tag.id))

    await session.flush()
    # reload with relationships
    return await _get_note_or_404(session, user_id=user.id, note_id=note.id)


# PUBLIC_INTERFACE
async def get_note(session: AsyncSession, *, user: User, note_id: uuid.UUID) -> Note:
    """PUBLIC_INTERFACE: Fetch a single note by id scoped to the user."""
    return await _get_note_or_404(session, user_id=user.id, note_id=note_id)


# PUBLIC_INTERFACE
async def list_notes(
    session: AsyncSession,
    *,
    user: User,
    offset: int,
    limit: int,
    tag: Optional[str],
    archived: Optional[bool],
) -> Tuple[List[Note], int]:
    """PUBLIC_INTERFACE: List notes for a user with optional tag/archived filters."""
    where_clauses = [Note.user_id == user.id]
    if archived is True:
        where_clauses.append(Note.archived_at.is_not(None))
    elif archived is False:
        where_clauses.append(Note.archived_at.is_(None))

    stmt = select(Note).where(and_(*where_clauses)).order_by(Note.updated_at.desc())
    count_stmt = select(func.count()).select_from(Note).where(and_(*where_clauses))

    if tag and tag.strip():
        # Join through tags for filtering.
        stmt = (
            stmt.join(NoteTag, NoteTag.note_id == Note.id)
            .join(Tag, Tag.id == NoteTag.tag_id)
            .where(and_(Tag.user_id == user.id, func.lower(Tag.name) == tag.strip().lower()))
        )
        count_stmt = (
            count_stmt.join(NoteTag, NoteTag.note_id == Note.id)
            .join(Tag, Tag.id == NoteTag.tag_id)
            .where(and_(Tag.user_id == user.id, func.lower(Tag.name) == tag.strip().lower()))
        )

    stmt = stmt.options(selectinload(Note.note_tags).selectinload(NoteTag.tag)).offset(offset).limit(limit)

    res = await session.execute(stmt)
    notes = res.scalars().unique().all()

    total_res = await session.execute(count_stmt)
    total = int(total_res.scalar_one())

    return notes, total


# PUBLIC_INTERFACE
async def update_note(
    session: AsyncSession,
    *,
    user: User,
    note_id: uuid.UUID,
    title: Optional[str],
    content: Optional[str],
    content_markdown: Optional[str],
    archived: Optional[bool],
    tags: Optional[List[str]],
) -> Note:
    """PUBLIC_INTERFACE: Update note fields/tags scoped to the user."""
    note = await _get_note_or_404(session, user_id=user.id, note_id=note_id)

    if title is not None:
        note.title = title
    if content is not None:
        note.content = content
    if content_markdown is not None:
        note.content_markdown = content_markdown
    if archived is not None:
        note.archived_at = datetime.now(timezone.utc) if archived else None

    if tags is not None:
        # Replace all tags for note.
        await session.execute(delete(NoteTag).where(NoteTag.note_id == note.id))
        tag_objs = await _get_or_create_tags(session, user_id=user.id, tag_names=tags)
        for tag in tag_objs:
            session.add(NoteTag(note_id=note.id, tag_id=tag.id))

    await session.flush()
    return await _get_note_or_404(session, user_id=user.id, note_id=note.id)


# PUBLIC_INTERFACE
async def delete_note(session: AsyncSession, *, user: User, note_id: uuid.UUID) -> None:
    """PUBLIC_INTERFACE: Delete note scoped to the user."""
    note = await _get_note_or_404(session, user_id=user.id, note_id=note_id)
    await session.delete(note)
    await session.flush()


# PUBLIC_INTERFACE
async def list_tags(session: AsyncSession, *, user: User) -> List[Tag]:
    """PUBLIC_INTERFACE: List all tags for a user."""
    res = await session.execute(select(Tag).where(Tag.user_id == user.id).order_by(func.lower(Tag.name)))
    return res.scalars().all()


# PUBLIC_INTERFACE
async def delete_tag(session: AsyncSession, *, user: User, tag_id: uuid.UUID) -> None:
    """PUBLIC_INTERFACE: Delete a tag (and note associations) scoped to the user."""
    res = await session.execute(select(Tag).where(and_(Tag.id == tag_id, Tag.user_id == user.id)))
    tag = res.scalar_one_or_none()
    if not tag:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Tag not found")
    await session.delete(tag)
    await session.flush()


# PUBLIC_INTERFACE
async def search_notes(
    session: AsyncSession,
    *,
    user: User,
    query: str,
    offset: int,
    limit: int,
) -> Tuple[List[Note], int]:
    """PUBLIC_INTERFACE: Search notes scoped to a user (FTS + trigram fallback)."""
    q = (query or "").strip()
    if not q:
        return [], 0

    # Prefer full-text search.
    ts_query = func.websearch_to_tsquery("english", q)

    fts_filter = Note.search_vector.op("@@")(ts_query)
    trigram_filter = or_(
        Note.title.op("%")(q),
        Note.content.op("%")(q),
        Note.content_markdown.op("%")(q),
        Note.title.ilike(f"%{q}%"),
        Note.content.ilike(f"%{q}%"),
    )
    combined_filter = and_(Note.user_id == user.id, or_(fts_filter, trigram_filter))

    stmt = (
        select(Note)
        .where(combined_filter)
        .order_by(Note.updated_at.desc())
        .options(selectinload(Note.note_tags).selectinload(NoteTag.tag))
        .offset(offset)
        .limit(limit)
    )
    count_stmt = select(func.count()).select_from(Note).where(combined_filter)

    res = await session.execute(stmt)
    notes = res.scalars().unique().all()

    total_res = await session.execute(count_stmt)
    total = int(total_res.scalar_one())

    return notes, total


# PUBLIC_INTERFACE
async def ensure_user_email_unique(session: AsyncSession, *, email: str) -> None:
    """PUBLIC_INTERFACE: Raise 409 if email already exists (case-insensitive due to citext)."""
    res = await session.execute(select(User.id).where(User.email == email))
    if res.scalar_one_or_none() is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")
