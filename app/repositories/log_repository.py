from datetime import datetime, timezone
from typing import Any

import asyncpg

from app.models.log import LogCreate, LogEntry, LogSource


class LogRepository:
    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn

    async def insert(self, log: LogCreate) -> dict:
        """Insert single log entry."""
        now = datetime.now(timezone.utc)
        timestamp = log.timestamp or now

        row = await self.conn.fetchrow(
            """
            INSERT INTO logs (
                timestamp, source_app, source_host, source_instance,
                severity, message, metadata, trace_id, span_id, created_at
            ) VALUES ($1, $2, $3, $4, $5, $6, $7, $8, $9, $10)
            RETURNING id, timestamp, created_at
            """,
            timestamp,
            log.source.app_id,
            log.source.host,
            log.source.instance_id,
            log.severity,
            log.message,
            log.metadata,
            log.trace_id,
            log.span_id,
            now,
        )

        return {
            "id": str(row["id"]),
            "timestamp": row["timestamp"],
            "created_at": row["created_at"],
        }

    async def get_by_id(self, log_id: str) -> LogEntry | None:
        """Get single log by ID."""
        row = await self.conn.fetchrow(
            "SELECT * FROM logs WHERE id = $1",
            int(log_id),
        )

        if not row:
            return None

        return self._row_to_entry(row)

    async def query(
        self,
        source_app: str | None = None,
        severity: str | None = None,
        search: str | None = None,
        trace_id: str | None = None,
        limit: int = 100,
        offset: int = 0,
        sort: str = "desc",
    ) -> tuple[list[LogEntry], int]:
        """Query logs with filters."""
        conditions = []
        params: list[Any] = []
        param_idx = 1

        if source_app:
            conditions.append(f"source_app = ${param_idx}")
            params.append(source_app)
            param_idx += 1

        if severity:
            severities = severity.split(",")
            placeholders = ", ".join(f"${param_idx + i}" for i in range(len(severities)))
            conditions.append(f"severity IN ({placeholders})")
            params.extend(severities)
            param_idx += len(severities)

        if search:
            conditions.append(f"message_search @@ plainto_tsquery('english', ${param_idx})")
            params.append(search)
            param_idx += 1

        if trace_id:
            conditions.append(f"trace_id = ${param_idx}")
            params.append(trace_id)
            param_idx += 1

        where_clause = " AND ".join(conditions) if conditions else "TRUE"
        order = "DESC" if sort == "desc" else "ASC"

        # Count total
        count_row = await self.conn.fetchrow(
            f"SELECT COUNT(*) as total FROM logs WHERE {where_clause}",
            *params,
        )
        total = count_row["total"]

        # Get rows
        rows = await self.conn.fetch(
            f"""
            SELECT * FROM logs
            WHERE {where_clause}
            ORDER BY timestamp {order}
            LIMIT ${param_idx} OFFSET ${param_idx + 1}
            """,
            *params,
            limit,
            offset,
        )

        return [self._row_to_entry(row) for row in rows], total

    def _row_to_entry(self, row: asyncpg.Record) -> LogEntry:
        """Convert database row to LogEntry."""
        return LogEntry(
            id=str(row["id"]),
            timestamp=row["timestamp"],
            source=LogSource(
                app_id=row["source_app"],
                host=row["source_host"],
                instance_id=row["source_instance"],
            ),
            severity=row["severity"],
            message=row["message"],
            metadata=row["metadata"],
            trace_id=row["trace_id"],
            span_id=row["span_id"],
            created_at=row["created_at"],
        )