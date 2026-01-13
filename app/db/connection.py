from contextlib import asynccontextmanager
from typing import AsyncGenerator

import asyncpg
from asyncpg import Pool

from app.config import get_settings

_pool: Pool | None = None


async def init_db() -> None:
    """Initialize database connection pool."""
    global _pool
    settings = get_settings()
    
    _pool = await asyncpg.create_pool(
        dsn=settings.database_url,
        min_size=5,
        max_size=settings.database_pool_size,
    )
    print(f"Database pool created (size: {settings.database_pool_size})")


async def close_db() -> None:
    """Close database connection pool."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
        print("Database pool closed")


def get_pool() -> Pool:
    """Get database pool."""
    if _pool is None:
        raise RuntimeError("Database pool not initialized")
    return _pool


@asynccontextmanager
async def get_connection() -> AsyncGenerator[asyncpg.Connection, None]:
    """Get a database connection from the pool."""
    pool = get_pool()
    async with pool.acquire() as conn:
        yield conn