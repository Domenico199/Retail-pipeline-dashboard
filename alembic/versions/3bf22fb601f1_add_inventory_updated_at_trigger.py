"""add_inventory_updated_at_trigger

Revision ID: 3bf22fb601f1
Revises: ad2b2eb4f887
Create Date: 2026-03-31 19:28:34.904971

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3bf22fb601f1'
down_revision: Union[str, Sequence[str], None] = 'ad2b2eb4f887'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create a reusable trigger function for auto-updating updated_at,
    then attach it to core.inventory."""

    # Create reusable trigger function (can be shared across tables)
    op.execute("""
        CREATE OR REPLACE FUNCTION core.update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = CURRENT_TIMESTAMP;
            RETURN NEW;
        END;
        $$ LANGUAGE plpgsql;
    """)

    # Attach trigger to core.inventory
    op.execute("""
        CREATE TRIGGER trg_inventory_updated_at
        BEFORE UPDATE ON core.inventory
        FOR EACH ROW
        EXECUTE FUNCTION core.update_updated_at_column();
    """)


def downgrade() -> None:
    """Remove trigger and function."""
    op.execute("DROP TRIGGER IF EXISTS trg_inventory_updated_at ON core.inventory;")
    op.execute("DROP FUNCTION IF EXISTS core.update_updated_at_column();")
