import uuid
from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, EmailStr, Field


class ApiMessage(BaseModel):
    message: str = Field(..., description="Human-readable status message.")


# -------------------------
# Auth
# -------------------------
class SignupRequest(BaseModel):
    email: EmailStr = Field(..., description="User email (unique, case-insensitive).")
    password: str = Field(..., min_length=8, description="Plaintext password (min 8 characters).")


class LoginRequest(BaseModel):
    email: EmailStr = Field(..., description="User email.")
    password: str = Field(..., description="Plaintext password.")


class TokenResponse(BaseModel):
    access_token: str = Field(..., description="JWT access token.")
    token_type: str = Field("bearer", description="Token type; always 'bearer'.")


class MeResponse(BaseModel):
    id: uuid.UUID = Field(..., description="User id.")
    email: EmailStr = Field(..., description="User email.")


# -------------------------
# Notes
# -------------------------
class NoteBase(BaseModel):
    title: str = Field("", description="Note title.")
    content: str = Field("", description="Plain text content.")
    content_markdown: str = Field("", description="Markdown content.")


class NoteCreateRequest(NoteBase):
    tags: List[str] = Field(default_factory=list, description="Initial tag names to attach.")


class NoteUpdateRequest(BaseModel):
    title: Optional[str] = Field(None, description="Updated title.")
    content: Optional[str] = Field(None, description="Updated plain text content.")
    content_markdown: Optional[str] = Field(None, description="Updated markdown content.")
    archived: Optional[bool] = Field(None, description="Archive/unarchive the note.")
    tags: Optional[List[str]] = Field(None, description="Replace tags with provided names.")


class NoteResponse(NoteBase):
    id: uuid.UUID = Field(..., description="Note id.")
    created_at: datetime = Field(..., description="Creation timestamp.")
    updated_at: datetime = Field(..., description="Last update timestamp.")
    archived_at: Optional[datetime] = Field(None, description="Archive timestamp if archived.")
    tags: List[str] = Field(default_factory=list, description="Tag names attached to this note.")


class NoteListResponse(BaseModel):
    items: List[NoteResponse] = Field(..., description="Notes list.")
    total: int = Field(..., description="Total number of notes matching query.")
    offset: int = Field(..., description="Pagination offset.")
    limit: int = Field(..., description="Pagination limit.")


# -------------------------
# Tags
# -------------------------
class TagResponse(BaseModel):
    id: uuid.UUID = Field(..., description="Tag id.")
    name: str = Field(..., description="Tag name.")
    created_at: datetime = Field(..., description="Creation timestamp.")


class TagListResponse(BaseModel):
    items: List[TagResponse] = Field(..., description="Tags list.")


# -------------------------
# Search
# -------------------------
class SearchResponse(BaseModel):
    items: List[NoteResponse] = Field(..., description="Notes matching the search query.")
    total: int = Field(..., description="Total matching notes.")
    offset: int = Field(..., description="Pagination offset.")
    limit: int = Field(..., description="Pagination limit.")
