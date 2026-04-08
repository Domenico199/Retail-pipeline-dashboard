"""create_shelf_movements_current

Revision ID: d4e5f6a7b8c9
Revises: c3d4e5f6a7b8
Create Date: 2026-04-07 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, None] = 'c3d4e5f6a7b8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("""
    CREATE VIEW analytics.shelf_movements_current AS
    SELECT
        sa.store_id,
        sa.shelf_id,
        sa.shelf_level,
        sa.zone,
        sa.slot_number,
        m.product_id,
        p.product_description,
        p.category_level_1,
        p.category_level_2,
        m.movement_type,
        m.quantity,
        m.unit_sale_price,
        m.unit_purchase_price,
        p.purchase_price AS unit_cost,
        m.is_promo,
        m.movement_date,
        TO_CHAR(m.movement_date, 'YYYY-MM')          AS month,
        EXTRACT(YEAR FROM m.movement_date)::INTEGER   AS year,
        EXTRACT(WEEK FROM m.movement_date)::INTEGER   AS week
    FROM core.movements m
    JOIN core.store_assortment sa
        ON sa.store_id = m.store_id
       AND sa.product_id = m.product_id
       AND sa.active_flag = TRUE
    JOIN core.products p ON p.product_id = m.product_id
    """)


def downgrade() -> None:
    op.execute("DROP VIEW IF EXISTS analytics.shelf_movements_current")
