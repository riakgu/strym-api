from datetime import datetime, timezone

from fastapi import APIRouter

from app.models.log import LogCreate, LogResponse

router = APIRouter(prefix="/logs", tags=["Ingestion"])


def generate_id() -> str:
    """Generate simple ID"""
    import time
    return f"log_{int(time.time() * 1000)}"


@router.post("", status_code=201)
async def ingest_log(log: LogCreate) -> LogResponse:
    """Ingest a single log entry."""
    now = datetime.now(timezone.utc)
    
    log_id = generate_id()
    timestamp = log.timestamp or now
    
    return LogResponse(
        id=log_id,
        timestamp=timestamp,
        created_at=now,
    )


@router.post("/bulk", status_code=202)
async def ingest_bulk(logs: list[LogCreate]) -> dict:
    """Ingest multiple logs."""
    now = datetime.now(timezone.utc)
    
    accepted = len(logs)
    
    return {
        "accepted": accepted,
        "rejected": 0,
        "errors": [],
        "batch_id": f"batch_{int(now.timestamp() * 1000)}",
    }