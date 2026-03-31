CREATE TABLE IF NOT EXISTS staging.pipeline_runs (
    run_id                BIGSERIAL PRIMARY KEY,

    pipeline_step         VARCHAR(50) NOT NULL,
    source_file_name      VARCHAR(255),

    status                VARCHAR(20) NOT NULL DEFAULT 'running',
    rows_processed        INTEGER,
    rows_success          INTEGER,
    rows_failed           INTEGER,
    error_message         TEXT,

    started_at            TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    completed_at          TIMESTAMP,
    duration_seconds      NUMERIC(10,2)
);

CREATE INDEX IF NOT EXISTS idx_pipeline_runs_step
    ON staging.pipeline_runs(pipeline_step);

CREATE INDEX IF NOT EXISTS idx_pipeline_runs_status
    ON staging.pipeline_runs(status);

CREATE INDEX IF NOT EXISTS idx_pipeline_runs_started
    ON staging.pipeline_runs(started_at);
