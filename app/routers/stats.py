from datetime import datetime, timezone

from fastapi import APIRouter, Query

router = APIRouter(prefix="/stats", tags=["Stats"])


@router.get("/summary")
async def get_summary(
    source_app: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
) -> dict:
    """Get high-level statistics."""
    
    now = datetime.now(timezone.utc)
    

    return {
        "time_range": {
            "start": start or now,
            "end": end or now,
        },
        "total_logs": 0,
        "by_severity": {
            "debug": 0,
            "info": 0,
            "warn": 0,
            "error": 0,
            "fatal": 0,
        },
        "error_rate": 0.0,
        "logs_per_second": {
            "avg": 0.0,
            "p95": 0.0,
            "p99": 0.0,
        },
    }


@router.get("/timeseries")
async def get_timeseries(
    start: datetime | None = None,
    end: datetime | None = None,
    interval: str = Query(default="5m", pattern=r"^(1m|5m|15m|1h|1d)$"),
    group_by: str = Query(default="severity", pattern=r"^(severity|source_app)$"),
    source_app: str | None = None,
) -> dict:
    """Time-series data for charts."""
    

    return {
        "interval": interval,
        "series": [],
    }