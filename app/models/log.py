from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class LogSource(BaseModel):
    app_id: str
    host: str | None = None
    instance_id: str | None = None


class LogCreate(BaseModel):
    timestamp: datetime | None = None
    source: LogSource
    severity: str = Field(pattern=r"^(debug|info|warn|error|fatal)$")
    message: str
    metadata: dict[str, Any] | None = None
    trace_id: str | None = None
    span_id: str | None = None


class LogResponse(BaseModel):
    id: str
    timestamp: datetime
    created_at: datetime


class LogEntry(BaseModel):
    id: str
    timestamp: datetime
    source: LogSource
    severity: str
    message: str
    metadata: dict[str, Any] | None = None
    trace_id: str | None = None
    span_id: str | None = None
    created_at: datetime