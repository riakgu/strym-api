from datetime import datetime, timezone

from fastapi import APIRouter, BackgroundTasks

from app.models.log import LogCreate, LogResponse
from app.dependencies import LogServiceDep
from app.services.stream_service import stream_service

router = APIRouter(prefix="/logs", tags=["Ingestion"])


@router.post("", status_code=201)
async def ingest_log(
    log: LogCreate,
    service: LogServiceDep,
    background_tasks: BackgroundTasks,
) -> LogResponse:
    """Ingest a single log entry."""
    result = await service.ingest(log)
    
    # Broadcast to WebSocket subscribers
    background_tasks.add_task(
        stream_service.broadcast_log,
        {
            "id": result.id,
            "timestamp": result.timestamp.isoformat(),
            "source": log.source.model_dump(),
            "severity": log.severity,
            "message": log.message,
            "metadata": log.metadata,
            "trace_id": log.trace_id,
            "span_id": log.span_id,
        }
    )
    
    return result


@router.post("/bulk", status_code=202)
async def ingest_bulk(logs: list[LogCreate], service: LogServiceDep) -> dict:
    """Ingest multiple logs."""
    now = datetime.now(timezone.utc)
    result = await service.ingest_bulk(logs)
    result["batch_id"] = f"batch_{int(now.timestamp() * 1000)}"
    return result