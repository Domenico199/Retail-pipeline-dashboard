"""
Helper for tracking pipeline runs in staging.pipeline_runs.

Usage:
    tracker = RunTracker(engine, "extract")
    tracker.start(source_file_name="movements_2026-01-01.csv")
    # ... do work ...
    tracker.complete(rows_processed=100, rows_success=95, rows_failed=5)
    # or on error:
    tracker.fail("Error message here")
"""

from sqlalchemy import text
from datetime import datetime


class RunTracker:
    def __init__(self, engine, pipeline_step: str):
        self.engine = engine
        self.pipeline_step = pipeline_step
        self.run_id = None
        self.started_at = None

    def start(self, source_file_name: str = None):
        """Insert a new run record with status='running'."""
        self.started_at = datetime.now()
        with self.engine.begin() as conn:
            result = conn.execute(
                text("""
                    INSERT INTO staging.pipeline_runs (pipeline_step, source_file_name, status, started_at)
                    VALUES (:step, :file, 'running', :started)
                    RETURNING run_id
                """),
                {"step": self.pipeline_step, "file": source_file_name, "started": self.started_at},
            )
            self.run_id = result.scalar()
        return self.run_id

    def complete(self, rows_processed: int = 0, rows_success: int = 0, rows_failed: int = 0):
        """Mark run as success with metrics."""
        now = datetime.now()
        duration = (now - self.started_at).total_seconds()
        with self.engine.begin() as conn:
            conn.execute(
                text("""
                    UPDATE staging.pipeline_runs
                    SET status = 'success',
                        rows_processed = :processed,
                        rows_success = :success,
                        rows_failed = :failed,
                        completed_at = :completed,
                        duration_seconds = :duration
                    WHERE run_id = :run_id
                """),
                {
                    "processed": rows_processed,
                    "success": rows_success,
                    "failed": rows_failed,
                    "completed": now,
                    "duration": round(duration, 2),
                    "run_id": self.run_id,
                },
            )

    def fail(self, error_message: str):
        """Mark run as failed with error message."""
        now = datetime.now()
        duration = (now - self.started_at).total_seconds()
        with self.engine.begin() as conn:
            conn.execute(
                text("""
                    UPDATE staging.pipeline_runs
                    SET status = 'failed',
                        error_message = :error,
                        completed_at = :completed,
                        duration_seconds = :duration
                    WHERE run_id = :run_id
                """),
                {
                    "error": error_message,
                    "completed": now,
                    "duration": round(duration, 2),
                    "run_id": self.run_id,
                },
            )
