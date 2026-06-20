"""
Async database engine, session factory, and base model.
"""

from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from backend.app.config import get_settings

settings = get_settings()

# ── Async Engine ─────────────────────────────────────────
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=settings.DEBUG,
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
)

# ── Session Factory ──────────────────────────────────────
async_session = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


# ── Base Model ───────────────────────────────────────────
class Base(DeclarativeBase):
    """Declarative base for all SQLAlchemy models."""
    pass


# ── Dependency ───────────────────────────────────────────
async def get_db() -> AsyncSession:
    """FastAPI dependency that yields an async database session."""
    async with async_session() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
