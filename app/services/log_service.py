from app.models.log import LogCreate, LogEntry, LogResponse
from app.models.common import Pagination
from app.repositories.log_repository import LogRepository
from app.core.exceptions import NotFoundError
from app.services.cache_service import cache_service

CACHE_PREFIX = "logs"


class LogService:
    def __init__(self, repo: LogRepository):
        self.repo = repo

    async def ingest(self, log: LogCreate) -> LogResponse:
        """Ingest a single log entry."""
        result = await self.repo.insert(log)
        
        # Invalidate query cache when new log is added
        await cache_service.invalidate_prefix(CACHE_PREFIX)
        
        return LogResponse(**result)

    async def ingest_bulk(self, logs: list[LogCreate]) -> dict:
        """Ingest multiple logs."""
        accepted = 0
        errors = []

        for i, log in enumerate(logs):
            try:
                await self.repo.insert(log)
                accepted += 1
            except Exception as e:
                errors.append({"index": i, "error": str(e)})

        # Invalidate cache after bulk insert
        if accepted > 0:
            await cache_service.invalidate_prefix(CACHE_PREFIX)

        return {
            "accepted": accepted,
            "rejected": len(errors),
            "errors": errors,
        }

    async def get_by_id(self, log_id: str) -> LogEntry:
        """Get single log by ID."""
        entry = await self.repo.get_by_id(log_id)
        if not entry:
            raise NotFoundError("Log", log_id)
        return entry

    async def query(
        self,
        source_app: str | None = None,
        severity: str | None = None,
        search: str | None = None,
        trace_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
        sort: str = "desc",
    ) -> dict:
        """Query logs with filters and pagination (cached)."""
        
        # Build cache key from params
        cache_params = {
            "source_app": source_app,
            "severity": severity,
            "search": search,
            "trace_id": trace_id,
            "limit": limit,
            "offset": offset,
            "sort": sort,
        }
        
        # Try cache first
        cached = await cache_service.get(CACHE_PREFIX, cache_params)
        if cached:
            # Reconstruct Pagination object
            cached["pagination"] = Pagination(**cached["pagination"])
            return cached
        
        # Query database
        entries, total = await self.repo.query(
            source_app=source_app,
            severity=severity,
            search=search,
            trace_id=trace_id,
            limit=limit,
            offset=offset,
            sort=sort,
        )

        result = {
            "logs": [e.model_dump() for e in entries],
            "pagination": Pagination(
                total=total,
                limit=limit,
                offset=offset,
                has_more=(offset + limit) < total,
            ),
        }
        
        # Cache result (60 seconds)
        await cache_service.set(CACHE_PREFIX, cache_params, {
            "logs": result["logs"],
            "pagination": result["pagination"].model_dump(),
        })
        
        return result