from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Query, Depends

from app.dependencies import StatsServiceDep
from app.core.security import verify_api_key

router = APIRouter(prefix="/stats", tags=["Stats"])


@router.get("/summary")
async def get_summary(
    service: StatsServiceDep,
    _: Annotated[str, Depends(verify_api_key)],
    source_app: str | None = None,
    start: datetime | None = None,
    end: datetime | None = None,
) -> dict:
    """Get high-level statistics."""
    return await service.get_summary(
        source_app=source_app,
        start=start,
        end=end,
    )


@router.get("/timeseries")
async def get_timeseries(
    service: StatsServiceDep,
    _: Annotated[str, Depends(verify_api_key)],
    start: datetime | None = None,
    end: datetime | None = None,
    interval: str = Query(default="5m", pattern=r"^(1m|5m|15m|1h|1d)$"),
    group_by: str = Query(default="severity", pattern=r"^(severity|source_app)$"),
    source_app: str | None = None,
) -> dict:
    """Time-series data for charts."""
    return await service.get_timeseries(
        start=start,
        end=end,
        interval=interval,
        group_by=group_by,
        source_app=source_app,
    )