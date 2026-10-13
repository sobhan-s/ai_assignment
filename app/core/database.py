"""
Database engine, sessionmaker, and session dependency generator.
"""

from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

# Create async SQLAlchemy engine
# pool_size and max_overflow help manage concurrent connections (pool concept requested by user)
engine = create_async_engine(
    settings.postgres_sqlalchemy_url,
    pool_size=10,
    max_overflow=20,
    echo=False,
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    autocommit=False,
    autoflush=False,
    expire_on_commit=False,
    class_=AsyncSession,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """FastAPI database session dependency."""
    async with AsyncSessionLocal() as session:
        yield session
