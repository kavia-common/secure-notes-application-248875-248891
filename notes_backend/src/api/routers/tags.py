import uuid
from typing import Annotated

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.auth import get_current_user
from src.api.db import get_db_session
from src.api.models import User
from src.api.schemas import TagListResponse, TagResponse
from src.api.services import delete_tag, list_tags

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get(
    "",
    response_model=TagListResponse,
    summary="List tags",
    description="List all tags belonging to the authenticated user.",
)
async def list_tags_endpoint(
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> TagListResponse:
    """List tags for current user."""
    tags = await list_tags(session, user=current_user)
    return TagListResponse(
        items=[TagResponse(id=t.id, name=t.name, created_at=t.created_at) for t in tags],
    )


@router.delete(
    "/{tag_id}",
    summary="Delete tag",
    description="Delete a tag by id (must belong to authenticated user).",
    status_code=status.HTTP_204_NO_CONTENT,
)
async def delete_tag_endpoint(
    tag_id: uuid.UUID,
    current_user: Annotated[User, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db_session)],
) -> None:
    """Delete a tag by id."""
    await delete_tag(session, user=current_user, tag_id=tag_id)
    await session.commit()
    return None
