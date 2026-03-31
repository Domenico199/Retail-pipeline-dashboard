"""remove_raw_movements_constraints

Revision ID: ad2b2eb4f887
Revises: 201a206eb191
Create Date: 2026-03-31 19:27:36.355408

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'ad2b2eb4f887'
down_revision: Union[str, Sequence[str], None] = '201a206eb191'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Remove FK and CHECK constraints from staging.raw_movements.
    Raw layer must accept all data — validation moves to transform step."""

    # Remove FK constraints
    op.drop_constraint("fk_raw_movements_product", "raw_movements", schema="staging", type_="foreignkey")
    op.drop_constraint("fk_raw_movements_supplier", "raw_movements", schema="staging", type_="foreignkey")

    # Remove price CHECK constraints
    op.drop_constraint("chk_raw_movements_sale_price", "raw_movements", schema="staging", type_="check")
    op.drop_constraint("chk_raw_movements_purchase_price", "raw_movements", schema="staging", type_="check")
    op.drop_constraint("chk_raw_movements_breakage_prices", "raw_movements", schema="staging", type_="check")


def downgrade() -> None:
    """Restore FK and CHECK constraints on staging.raw_movements."""

    op.create_foreign_key(
        "fk_raw_movements_product", "raw_movements", "products",
        ["product_id"], ["product_id"],
        source_schema="staging", referent_schema="core",
        ondelete="CASCADE",
    )
    op.create_foreign_key(
        "fk_raw_movements_supplier", "raw_movements", "suppliers",
        ["supplier_id"], ["supplier_id"],
        source_schema="staging", referent_schema="core",
        ondelete="SET NULL",
    )
    op.create_check_constraint(
        "chk_raw_movements_sale_price", "raw_movements",
        "(movement_type <> 'sale') OR (unit_sale_price IS NOT NULL AND unit_sale_price > 0)",
        schema="staging",
    )
    op.create_check_constraint(
        "chk_raw_movements_purchase_price", "raw_movements",
        "(movement_type <> 'purchase') OR (unit_purchase_price IS NOT NULL AND unit_purchase_price > 0)",
        schema="staging",
    )
    op.create_check_constraint(
        "chk_raw_movements_breakage_prices", "raw_movements",
        "(movement_type <> 'breakage') OR (unit_sale_price IS NULL AND unit_purchase_price IS NULL)",
        schema="staging",
    )
