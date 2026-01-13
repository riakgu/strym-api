from datetime import datetime, timezone

from fastapi import APIRouter

from app.models.log import LogCreate, LogResponse
from app.dependencies import LogServiceDep

router = APIRouter(prefix="/logs", tags=["Ingestion"])


@router.post("", status_code=201)
async def ingest_log(log: LogCreate, service: LogServiceDep) -> LogResponse:
    """Ingest a single log entry."""
    return await service.ingest(log)


@router.post("/bulk", status_code=202)
async def ingest_bulk(logs: list[LogCreate], service: LogServiceDep) -> dict:
    """Ingest multiple logs."""
    now = datetime.now(timezone.utc)
    result = await service.ingest_bulk(logs)
    result["batch_id"] = f"batch_{int(now.timestamp() * 1000)}"
    return result