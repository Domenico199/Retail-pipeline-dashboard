"""add_cogs_breakage_cost_to_daily_kpis

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-04-03 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("DROP VIEW IF EXISTS analytics.daily_kpis")
    op.execute("""
    CREATE VIEW analytics.daily_kpis AS
    SELECT
        m.store_id,
        m.movement_date,
        COUNT(*)    FILTER (WHERE m.movement_type = 'sale')      AS sale_transactions,
        COALESCE(SUM(m.quantity) FILTER (WHERE m.movement_type = 'sale'), 0)      AS qty_sold,
        COALESCE(SUM(m.quantity * m.unit_sale_price) FILTER (WHERE m.movement_type = 'sale'), 0) AS revenue,
        COALESCE(SUM(m.quantity * p.purchase_price) FILTER (WHERE m.movement_type = 'sale'), 0) AS cogs,
        COUNT(*)    FILTER (WHERE m.movement_type = 'breakage')  AS breakage_events,
        COALESCE(SUM(m.quantity) FILTER (WHERE m.movement_type = 'breakage'), 0)  AS qty_breakage,
        COALESCE(SUM(m.quantity * p.purchase_price) FILTER (WHERE m.movement_type = 'breakage'), 0) AS breakage_cost,
        COUNT(*)    FILTER (WHERE m.movement_type = 'purchase')  AS purchase_transactions,
        COALESCE(SUM(m.quantity) FILTER (WHERE m.movement_type = 'purchase'), 0)  AS qty_purchased,
        COALESCE(SUM(m.quantity * m.unit_purchase_price) FILTER (WHERE m.movement_type = 'purchase'), 0) AS purchase_cost,
        COUNT(*)                                                 AS total_movements
    FROM core.movements m
    JOIN core.products p ON p.product_id = m.product_id
    GROUP BY m.store_id, m.movement_date
    """)


def downgrade() -> None:
    op.execute("""
    CREATE OR REPLACE VIEW analytics.daily_kpis AS
    SELECT
        m.store_id,
        m.movement_date,
        COUNT(*)    FILTER (WHERE m.movement_type = 'sale')      AS sale_transactions,
        COALESCE(SUM(m.quantity) FILTER (WHERE m.movement_type = 'sale'), 0)      AS qty_sold,
        COALESCE(SUM(m.quantity * m.unit_sale_price) FILTER (WHERE m.movement_type = 'sale'), 0) AS revenue,
        COUNT(*)    FILTER (WHERE m.movement_type = 'breakage')  AS breakage_events,
        COALESCE(SUM(m.quantity) FILTER (WHERE m.movement_type = 'breakage'), 0)  AS qty_breakage,
        COUNT(*)    FILTER (WHERE m.movement_type = 'purchase')  AS purchase_transactions,
        COALESCE(SUM(m.quantity) FILTER (WHERE m.movement_type = 'purchase'), 0)  AS qty_purchased,
        COALESCE(SUM(m.quantity * m.unit_purchase_price) FILTER (WHERE m.movement_type = 'purchase'), 0) AS purchase_cost,
        COUNT(*)                                                 AS total_movements
    FROM core.movements m
    GROUP BY m.store_id, m.movement_date
    """)
