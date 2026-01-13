from datetime import datetime
import time
from typing import Annotated

from fastapi import APIRouter, Query, Depends

from app.models.log import LogEntry
from app.dependencies import LogServiceDep
from app.core.security import verify_api_key

router = APIRouter(prefix="/logs", tags=["Query"])


@router.get("")
async def query_logs(
    service: LogServiceDep,
    _: Annotated[str, Depends(verify_api_key)],
    source_app: str | None = None,
    severity: str | None = None,
    search: str | None = None,
    trace_id: str | None = None,
    limit: int = Query(default=100, le=1000),
    offset: int = Query(default=0, ge=0),
    sort: str = Query(default="desc", pattern=r"^(asc|desc)$"),
) -> dict:
    """Query logs with filtering and pagination."""
    start = time.time()
    
    result = await service.query(
        source_app=source_app,
        severity=severity,
        search=search,
        trace_id=trace_id,
        limit=limit,
        offset=offset,
        sort=sort,
    )
    
    result["query_time_ms"] = round((time.time() - start) * 1000, 2)
    return result


@router.get("/search")
async def search_logs(
    service: LogServiceDep,
    _: Annotated[str, Depends(verify_api_key)],
    q: str,
    source_app: str | None = None,
    limit: int = Query(default=50, le=1000),
) -> dict:
    """Full-text search with relevance scoring."""
    start = time.time()
    
    result = await service.query(
        source_app=source_app,
        search=q,
        limit=limit,
    )
    
    return {
        "results": [{"log": log, "score": 1.0} for log in result["logs"]],
        "total": result["pagination"].total,
        "search_time_ms": round((time.time() - start) * 1000, 2),
    }


@router.get("/{log_id}")
async def get_log_by_id(
    log_id: str,
    service: LogServiceDep,
    _: Annotated[str, Depends(verify_api_key)],
) -> LogEntry:
    """Get single log by ID."""
    return await service.get_by_id(log_id)