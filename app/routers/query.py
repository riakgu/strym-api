from fastapi import APIRouter, Query

from app.models.log import LogEntry
from app.models.common import Pagination

router = APIRouter(prefix="/logs", tags=["Query"])


@router.get("")
async def query_logs(
    source_app: str | None = None,
    severity: str | None = None,
    search: str | None = None,
    trace_id: str | None = None,
    limit: int = Query(default=100, le=1000),
    offset: int = Query(default=0, ge=0),
    sort: str = Query(default="desc", pattern=r"^(asc|desc)$"),
) -> dict:
    """Query logs with filtering and pagination."""
    
    logs: list[LogEntry] = []
    
    return {
        "logs": logs,
        "pagination": Pagination(
            total=0,
            limit=limit,
            offset=offset,
            has_more=False,
        ),
        "query_time_ms": 0,
    }


@router.get("/search")
async def search_logs(
    q: str,
    source_app: str | None = None,
    limit: int = Query(default=50, le=1000),
) -> dict:
    """Full-text search with relevance scoring."""
    
    return {
        "results": [],
        "total": 0,
        "search_time_ms": 0,
    }


@router.get("/{log_id}")
async def get_log_by_id(log_id: str) -> dict:
    """Get single log by ID."""
    
    return {
        "error": "Not found",
    }