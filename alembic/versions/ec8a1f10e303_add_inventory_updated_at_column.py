"""add_inventory_updated_at_column

Revision ID: ec8a1f10e303
Revises: 07c7eb570292
Create Date: 2026-03-31 19:32:56.606622

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ec8a1f10e303'
down_revision: Union[str, Sequence[str], None] = '07c7eb570292'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add updated_at column to core.inventory (was missing from live DB
    despite being in DDL). The trigger from migration 3bf22fb601f1 already
    exists and will now work correctly."""
    op.add_column(
        "inventory",
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now()),
        schema="core",
    )


def downgrade() -> None:
    """Remove updated_at column from core.inventory."""
    op.drop_column("inventory", "updated_at", schema="core")
