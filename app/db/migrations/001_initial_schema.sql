-- Create logs table
CREATE TABLE IF NOT EXISTS logs (
    id BIGSERIAL,
    timestamp TIMESTAMPTZ NOT NULL,
    
    -- Source
    source_app TEXT NOT NULL,
    source_host TEXT,
    source_instance TEXT,
    
    -- Log
    severity TEXT NOT NULL,
    message TEXT NOT NULL,
    metadata JSONB,
    
    -- Tracing
    trace_id TEXT,
    span_id TEXT,
    
    -- Full-text search
    message_search tsvector GENERATED ALWAYS AS (
        to_tsvector('english', message)
    ) STORED,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- TimescaleDB requires timestamp in primary key
    PRIMARY KEY (id, timestamp),
    
    CHECK (severity IN ('debug', 'info', 'warn', 'error', 'fatal'))
);

-- Convert to hypertable (TimescaleDB)
SELECT create_hypertable('logs', 'timestamp', chunk_time_interval => INTERVAL '1 day');

-- Indexes
CREATE INDEX IF NOT EXISTS idx_logs_timestamp ON logs (timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_logs_source_time ON logs (source_app, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_logs_severity_time ON logs (severity, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_logs_trace ON logs (trace_id) WHERE trace_id IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_logs_fts ON logs USING GIN (message_search);
CREATE INDEX IF NOT EXISTS idx_logs_metadata ON logs USING GIN (metadata);