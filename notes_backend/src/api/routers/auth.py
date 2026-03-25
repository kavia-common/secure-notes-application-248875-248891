from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.auth import create_access_token, get_current_user, hash_password, verify_password
from src.api.db import get_db_session
from src.api.models import User
from src.api.schemas import ApiMessage, LoginRequest, MeResponse, SignupRequest, TokenResponse
from src.api.services import ensure_user_email_unique

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post(
    "/signup",
    response_model=TokenResponse,
    summary="Sign up",
    description="Create a new user account and return a JWT access token.",
    status_code=status.HTTP_201_CREATED,
)
async def signup(payload: SignupRequest, session: Annotated[AsyncSession, Depends(get_db_session)]) -> TokenResponse:
    """
    Create a user account.

    - **email**: unique email address (case-insensitive)
    - **password**: plaintext password (min 8 chars)

    Returns a bearer token to use as `Authorization: Bearer <token>`.
    """
    await ensure_user_email_unique(session, email=str(payload.email))

    user = User(email=str(payload.email), password_hash=hash_password(payload.password))
    session.add(user)
    await session.commit()
    await session.refresh(user)

    token = create_access_token(user_id=user.id, email=user.email)
    return TokenResponse(access_token=token)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Login",
    description="Verify credentials and return a JWT access token.",
)
async def login(payload: LoginRequest, session: Annotated[AsyncSession, Depends(get_db_session)]) -> TokenResponse:
    """
    Authenticate with email + password.

    Returns a bearer token to use as `Authorization: Bearer <token>`.
    """
    res = await session.execute(select(User).where(User.email == str(payload.email)))
    user = res.scalar_one_or_none()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid email or password")

    token = create_access_token(user_id=user.id, email=user.email)
    return TokenResponse(access_token=token)


@router.get(
    "/me",
    response_model=MeResponse,
    summary="Get current user",
    description="Return the current authenticated user.",
)
async def me(current_user: Annotated[User, Depends(get_current_user)]) -> MeResponse:
    """Return the authenticated user's profile."""
    return MeResponse(id=current_user.id, email=current_user.email)


@router.post(
    "/logout",
    response_model=ApiMessage,
    summary="Logout",
    description="Stateless JWT logout (client should discard token).",
)
async def logout(_: Annotated[User, Depends(get_current_user)]) -> ApiMessage:
    """
    JWT is stateless; to 'logout' the client must discard its token.
    This endpoint exists to match typical frontend flows.
    """
    return ApiMessage(message="Logged out")
