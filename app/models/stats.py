from datetime import datetime

from pydantic import BaseModel


class TimeRange(BaseModel):
    start: datetime
    end: datetime


class StatsSummary(BaseModel):
    time_range: TimeRange
    total_logs: int
    by_severity: dict[str, int]
    error_rate: float
    logs_per_second: dict[str, float]


class TimeSeriesPoint(BaseModel):
    timestamp: datetime
    values: dict[str, int]