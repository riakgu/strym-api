from typing import Annotated, AsyncGenerator

from fastapi import Depends
import asyncpg

from app.db.connection import get_pool
from app.repositories.log_repository import LogRepository
from app.repositories.stats_repository import StatsRepository
from app.services.log_service import LogService
from app.services.stats_service import StatsService


async def get_db_connection() -> AsyncGenerator[asyncpg.Connection, None]:
    """Get database connection from pool."""
    pool = get_pool()
    async with pool.acquire() as conn:
        yield conn


async def get_log_repository(
    conn: Annotated[asyncpg.Connection, Depends(get_db_connection)]
) -> LogRepository:
    """Get log repository instance."""
    return LogRepository(conn)


async def get_stats_repository(
    conn: Annotated[asyncpg.Connection, Depends(get_db_connection)]
) -> StatsRepository:
    """Get stats repository instance."""
    return StatsRepository(conn)


async def get_log_service(
    repo: Annotated[LogRepository, Depends(get_log_repository)]
) -> LogService:
    """Get log service instance."""
    return LogService(repo)


async def get_stats_service(
    repo: Annotated[StatsRepository, Depends(get_stats_repository)]
) -> StatsService:
    """Get stats service instance."""
    return StatsService(repo)


# Type aliases for cleaner signatures
DbConnection = Annotated[asyncpg.Connection, Depends(get_db_connection)]
LogRepoDep = Annotated[LogRepository, Depends(get_log_repository)]
LogServiceDep = Annotated[LogService, Depends(get_log_service)]
StatsRepoDep = Annotated[StatsRepository, Depends(get_stats_repository)]
StatsServiceDep = Annotated[StatsService, Depends(get_stats_service)]