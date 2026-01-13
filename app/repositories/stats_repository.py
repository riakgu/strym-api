from datetime import datetime, timezone

import asyncpg


class StatsRepository:
    def __init__(self, conn: asyncpg.Connection):
        self.conn = conn

    async def get_summary(
        self,
        source_app: str | None = None,
        start: datetime | None = None,
        end: datetime | None = None,
    ) -> dict:
        """Get aggregated statistics."""
        now = datetime.now(timezone.utc)
        start = start or now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = end or now

        conditions = ["timestamp >= $1", "timestamp <= $2"]
        params: list = [start, end]
        param_idx = 3

        if source_app:
            conditions.append(f"source_app = ${param_idx}")
            params.append(source_app)

        where_clause = " AND ".join(conditions)

        # Total count
        total_row = await self.conn.fetchrow(
            f"SELECT COUNT(*) as total FROM logs WHERE {where_clause}",
            *params,
        )
        total = total_row["total"]

        # Count by severity
        severity_rows = await self.conn.fetch(
            f"""
            SELECT severity, COUNT(*) as count
            FROM logs
            WHERE {where_clause}
            GROUP BY severity
            """,
            *params,
        )
        by_severity = {row["severity"]: row["count"] for row in severity_rows}

        # Fill missing severities
        for sev in ["debug", "info", "warn", "error", "fatal"]:
            if sev not in by_severity:
                by_severity[sev] = 0

        # Error rate
        error_count = by_severity.get("error", 0) + by_severity.get("fatal", 0)
        error_rate = error_count / total if total > 0 else 0.0

        # Logs per second
        duration_seconds = (end - start).total_seconds()
        avg_per_second = total / duration_seconds if duration_seconds > 0 else 0.0

        return {
            "time_range": {"start": start, "end": end},
            "total_logs": total,
            "by_severity": by_severity,
            "error_rate": round(error_rate, 4),
            "logs_per_second": {
                "avg": round(avg_per_second, 2),
                "p95": 0.0,  # TODO: implement percentile
                "p99": 0.0,
            },
        }

    async def get_timeseries(
        self,
        start: datetime | None = None,
        end: datetime | None = None,
        interval: str = "5m",
        group_by: str = "severity",
        source_app: str | None = None,
    ) -> list[dict]:
        """Get time-series data for charts."""
        now = datetime.now(timezone.utc)
        start = start or now.replace(hour=0, minute=0, second=0, microsecond=0)
        end = end or now

        # Convert interval to PostgreSQL format
        interval_map = {
            "1m": "1 minute",
            "5m": "5 minutes",
            "15m": "15 minutes",
            "1h": "1 hour",
            "1d": "1 day",
        }
        pg_interval = interval_map.get(interval, "5 minutes")

        conditions = ["timestamp >= $1", "timestamp <= $2"]
        params: list = [start, end]
        param_idx = 3

        if source_app:
            conditions.append(f"source_app = ${param_idx}")
            params.append(source_app)

        where_clause = " AND ".join(conditions)

        rows = await self.conn.fetch(
            f"""
            SELECT 
                time_bucket('{pg_interval}', timestamp) as bucket,
                {group_by},
                COUNT(*) as count
            FROM logs
            WHERE {where_clause}
            GROUP BY bucket, {group_by}
            ORDER BY bucket
            """,
            *params,
        )

        # Aggregate into series format
        series_map: dict[datetime, dict] = {}
        for row in rows:
            bucket = row["bucket"]
            if bucket not in series_map:
                series_map[bucket] = {"timestamp": bucket, "values": {}}
            series_map[bucket]["values"][row[group_by]] = row["count"]

        return list(series_map.values())