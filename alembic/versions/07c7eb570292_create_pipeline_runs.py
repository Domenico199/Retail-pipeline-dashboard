"""create_pipeline_runs

Revision ID: 07c7eb570292
Revises: 3bf22fb601f1
Create Date: 2026-03-31 19:28:51.379697

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '07c7eb570292'
down_revision: Union[str, Sequence[str], None] = '3bf22fb601f1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create staging.pipeline_runs for pipeline observability."""
    op.create_table(
        "pipeline_runs",
        sa.Column("run_id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("pipeline_step", sa.String(50), nullable=False),
        sa.Column("source_file_name", sa.String(255), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="running"),
        sa.Column("rows_processed", sa.Integer, nullable=True),
        sa.Column("rows_success", sa.Integer, nullable=True),
        sa.Column("rows_failed", sa.Integer, nullable=True),
        sa.Column("error_message", sa.Text, nullable=True),
        sa.Column("started_at", sa.DateTime, nullable=False, server_default=sa.func.now()),
        sa.Column("completed_at", sa.DateTime, nullable=True),
        sa.Column("duration_seconds", sa.Numeric(10, 2), nullable=True),
        schema="staging",
    )

    op.create_index("idx_pipeline_runs_step", "pipeline_runs", ["pipeline_step"], schema="staging")
    op.create_index("idx_pipeline_runs_status", "pipeline_runs", ["status"], schema="staging")
    op.create_index("idx_pipeline_runs_started", "pipeline_runs", ["started_at"], schema="staging")


def downgrade() -> None:
    """Drop staging.pipeline_runs."""
    op.drop_table("pipeline_runs", schema="staging")
