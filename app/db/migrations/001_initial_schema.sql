-- Create logs table
CREATE TABLE IF NOT EXISTS logs (
    id BIGSERIAL PRIMARY KEY,
    timestamp TIMESTAMPTZ NOT NULL,
    
    -- Source
    source_app VARCHAR(100) NOT NULL,
    source_host VARCHAR(255),
    source_instance VARCHAR(100),
    
    -- Log
    severity VARCHAR(20) NOT NULL,
    message TEXT NOT NULL,
    metadata JSONB,
    
    -- Tracing
    trace_id VARCHAR(64),
    span_id VARCHAR(32),
    
    -- Full-text search
    message_search tsvector GENERATED ALWAYS AS (
        to_tsvector('english', message)
    ) STORED,
    
    created_at TIMESTAMPTZ DEFAULT NOW(),
    
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