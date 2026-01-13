from datetime import datetime

from app.repositories.stats_repository import StatsRepository


class StatsService:
    def __init__(self, repo: StatsRepository):
        self.repo = repo

    async def get_summary(
        self,
        source_app: str | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> dict:
        """Get aggregated statistics."""
        return await self.repo.get_summary(
            source_app=source_app,
            start=start,
            end=end,
        )

    async def get_timeseries(
        self,
        start: datetime | None = None,
        end: datetime | None = None,
        interval: str = "5m",
        group_by: str = "severity",
        source_app: str | None = None,
    ) -> dict:
        """Get time-series data for charts."""
        series = await self.repo.get_timeseries(
            start=start,
            end=end,
            interval=interval,
            group_by=group_by,
            source_app=source_app,
        )
        return {
            "interval": interval,
            "series": series,
        }
