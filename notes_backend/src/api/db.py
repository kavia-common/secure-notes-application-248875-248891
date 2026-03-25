from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, async_sessionmaker, create_async_engine

from src.api.config import get_settings

_settings = get_settings()


def _make_async_sqlalchemy_url() -> str:
    """
    Convert a postgres URL into an asyncpg SQLAlchemy URL.

    POSTGRES_URL is expected to be like: postgresql://host:port/db
    """
    url = _settings.postgres_url
    if url.startswith("postgresql+asyncpg://"):
        return url
    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)
    # Fallback: assume it's already compatible.
    return url


engine: AsyncEngine = create_async_engine(
    _make_async_sqlalchemy_url(),
    pool_pre_ping=True,
)

async_session_factory: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    expire_on_commit=False,
    class_=AsyncSession,
)


# PUBLIC_INTERFACE
async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """PUBLIC_INTERFACE: FastAPI dependency that yields an AsyncSession."""
    async with async_session_factory() as session:
        yield session
