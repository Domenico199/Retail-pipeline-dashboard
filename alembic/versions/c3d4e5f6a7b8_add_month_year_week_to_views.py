"""add_month_year_week_to_analytics_views

Revision ID: c3d4e5f6a7b8
Revises: b2c3d4e5f6a7
Create Date: 2026-04-04 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = 'c3d4e5f6a7b8'
down_revision: Union[str, None] = 'b2c3d4e5f6a7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

DATE_COLS = """
    TO_CHAR(m.movement_date, 'YYYY-MM')              AS month,
    EXTRACT(YEAR FROM m.movement_date)::INTEGER       AS year,
    EXTRACT(WEEK FROM m.movement_date)::INTEGER       AS week,"""


def upgrade() -> None:
    # Drop all 6 views (order doesn't matter, no dependencies between them)
    for v in ['sales_by_shelf_historical', 'sales_by_shelf_current',
              'breakage_by_shelf_historical', 'breakage_by_shelf_current',
              'margins_by_product_shelf', 'daily_kpis']:
        op.execute(f"DROP VIEW IF EXISTS analytics.{v}")

    # 1. sales_by_shelf_historical
    op.execute(f"""
    CREATE VIEW analytics.sales_by_shelf_historical AS
    SELECT
        m.store_id,
        m.shelf_id,
        m.movement_date,
        {DATE_COLS}
        COUNT(*)            AS transaction_count,
        SUM(m.quantity)     AS qty_sold,
        SUM(m.quantity * m.unit_sale_price) AS revenue
    FROM core.movements m
    WHERE m.movement_type = 'sale'
      AND m.shelf_id IS NOT NULL
    GROUP BY m.store_id, m.shelf_id, m.movement_date
    """)

    # 2. sales_by_shelf_current
    op.execute(f"""
    CREATE VIEW analytics.sales_by_shelf_current AS
    SELECT
        m.store_id,
        sa.shelf_id,
        m.movement_date,
        {DATE_COLS}
        COUNT(*)            AS transaction_count,
        SUM(m.quantity)     AS qty_sold,
        SUM(m.quantity * m.unit_sale_price) AS revenue
    FROM core.movements m
    JOIN core.store_assortment sa
        ON sa.store_id = m.store_id
       AND sa.product_id = m.product_id
       AND sa.active_flag = TRUE
    WHERE m.movement_type = 'sale'
    GROUP BY m.store_id, sa.shelf_id, m.movement_date
    """)

    # 3. breakage_by_shelf_historical
    op.execute(f"""
    CREATE VIEW analytics.breakage_by_shelf_historical AS
    SELECT
        m.store_id,
        m.shelf_id,
        m.movement_date,
        {DATE_COLS}
        COUNT(*)            AS breakage_events,
        SUM(m.quantity)     AS qty_lost,
        SUM(m.quantity * p.purchase_price) AS breakage_cost
    FROM core.movements m
    JOIN core.products p ON p.product_id = m.product_id
    WHERE m.movement_type = 'breakage'
      AND m.shelf_id IS NOT NULL
    GROUP BY m.store_id, m.shelf_id, m.movement_date
    """)

    # 4. breakage_by_shelf_current
    op.execute(f"""
    CREATE VIEW analytics.breakage_by_shelf_current AS
    SELECT
        m.store_id,
        sa.shelf_id,
        m.movement_date,
        {DATE_COLS}
        COUNT(*)            AS breakage_events,
        SUM(m.quantity)     AS qty_lost,
        SUM(m.quantity * p.purchase_price) AS breakage_cost
    FROM core.movements m
    JOIN core.products p ON p.product_id = m.product_id
    JOIN core.store_assortment sa
        ON sa.store_id = m.store_id
       AND sa.product_id = m.product_id
       AND sa.active_flag = TRUE
    WHERE m.movement_type = 'breakage'
    GROUP BY m.store_id, sa.shelf_id, m.movement_date
    """)

    # 5. margins_by_product_shelf
    op.execute(f"""
    CREATE VIEW analytics.margins_by_product_shelf AS
    SELECT
        m.store_id,
        m.product_id,
        p.product_description,
        p.category_level_1,
        p.category_level_2,
        m.shelf_id,
        m.movement_date,
        {DATE_COLS}
        SUM(m.quantity)                          AS qty_sold,
        SUM(m.quantity * m.unit_sale_price)      AS revenue,
        SUM(m.quantity * p.purchase_price)       AS cost,
        SUM(m.quantity * m.unit_sale_price)
          - SUM(m.quantity * p.purchase_price)   AS margin,
        CASE
            WHEN SUM(m.quantity * m.unit_sale_price) = 0 THEN 0
            ELSE ROUND(
                (SUM(m.quantity * m.unit_sale_price) - SUM(m.quantity * p.purchase_price))
                / SUM(m.quantity * m.unit_sale_price) * 100, 2
            )
        END AS margin_pct
    FROM core.movements m
    JOIN core.products p ON p.product_id = m.product_id
    WHERE m.movement_type = 'sale'
    GROUP BY m.store_id, m.product_id, p.product_description,
             p.category_level_1, p.category_level_2,
             m.shelf_id, m.movement_date
    """)

    # 6. daily_kpis
    op.execute(f"""
    CREATE VIEW analytics.daily_kpis AS
    SELECT
        m.store_id,
        m.movement_date,
        {DATE_COLS}
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
    # Drop and recreate without month/year/week columns
    for v in ['sales_by_shelf_historical', 'sales_by_shelf_current',
              'breakage_by_shelf_historical', 'breakage_by_shelf_current',
              'margins_by_product_shelf', 'daily_kpis']:
        op.execute(f"DROP VIEW IF EXISTS analytics.{v}")

    op.execute("""
    CREATE VIEW analytics.sales_by_shelf_historical AS
    SELECT m.store_id, m.shelf_id, m.movement_date,
        COUNT(*) AS transaction_count, SUM(m.quantity) AS qty_sold,
        SUM(m.quantity * m.unit_sale_price) AS revenue
    FROM core.movements m WHERE m.movement_type = 'sale' AND m.shelf_id IS NOT NULL
    GROUP BY m.store_id, m.shelf_id, m.movement_date
    """)

    op.execute("""
    CREATE VIEW analytics.sales_by_shelf_current AS
    SELECT m.store_id, sa.shelf_id, m.movement_date,
        COUNT(*) AS transaction_count, SUM(m.quantity) AS qty_sold,
        SUM(m.quantity * m.unit_sale_price) AS revenue
    FROM core.movements m
    JOIN core.store_assortment sa ON sa.store_id = m.store_id AND sa.product_id = m.product_id AND sa.active_flag = TRUE
    WHERE m.movement_type = 'sale'
    GROUP BY m.store_id, sa.shelf_id, m.movement_date
    """)

    op.execute("""
    CREATE VIEW analytics.breakage_by_shelf_historical AS
    SELECT m.store_id, m.shelf_id, m.movement_date,
        COUNT(*) AS breakage_events, SUM(m.quantity) AS qty_lost,
        SUM(m.quantity * p.purchase_price) AS breakage_cost
    FROM core.movements m JOIN core.products p ON p.product_id = m.product_id
    WHERE m.movement_type = 'breakage' AND m.shelf_id IS NOT NULL
    GROUP BY m.store_id, m.shelf_id, m.movement_date
    """)

    op.execute("""
    CREATE VIEW analytics.breakage_by_shelf_current AS
    SELECT m.store_id, sa.shelf_id, m.movement_date,
        COUNT(*) AS breakage_events, SUM(m.quantity) AS qty_lost,
        SUM(m.quantity * p.purchase_price) AS breakage_cost
    FROM core.movements m
    JOIN core.products p ON p.product_id = m.product_id
    JOIN core.store_assortment sa ON sa.store_id = m.store_id AND sa.product_id = m.product_id AND sa.active_flag = TRUE
    WHERE m.movement_type = 'breakage'
    GROUP BY m.store_id, sa.shelf_id, m.movement_date
    """)

    op.execute("""
    CREATE VIEW analytics.margins_by_product_shelf AS
    SELECT m.store_id, m.product_id, p.product_description, p.category_level_1, p.category_level_2,
        m.shelf_id, m.movement_date,
        SUM(m.quantity) AS qty_sold, SUM(m.quantity * m.unit_sale_price) AS revenue,
        SUM(m.quantity * p.purchase_price) AS cost,
        SUM(m.quantity * m.unit_sale_price) - SUM(m.quantity * p.purchase_price) AS margin,
        CASE WHEN SUM(m.quantity * m.unit_sale_price) = 0 THEN 0
            ELSE ROUND((SUM(m.quantity * m.unit_sale_price) - SUM(m.quantity * p.purchase_price))
            / SUM(m.quantity * m.unit_sale_price) * 100, 2) END AS margin_pct
    FROM core.movements m JOIN core.products p ON p.product_id = m.product_id
    WHERE m.movement_type = 'sale'
    GROUP BY m.store_id, m.product_id, p.product_description, p.category_level_1, p.category_level_2, m.shelf_id, m.movement_date
    """)

    op.execute("""
    CREATE VIEW analytics.daily_kpis AS
    SELECT m.store_id, m.movement_date,
        COUNT(*) FILTER (WHERE m.movement_type = 'sale') AS sale_transactions,
        COALESCE(SUM(m.quantity) FILTER (WHERE m.movement_type = 'sale'), 0) AS qty_sold,
        COALESCE(SUM(m.quantity * m.unit_sale_price) FILTER (WHERE m.movement_type = 'sale'), 0) AS revenue,
        COALESCE(SUM(m.quantity * p.purchase_price) FILTER (WHERE m.movement_type = 'sale'), 0) AS cogs,
        COUNT(*) FILTER (WHERE m.movement_type = 'breakage') AS breakage_events,
        COALESCE(SUM(m.quantity) FILTER (WHERE m.movement_type = 'breakage'), 0) AS qty_breakage,
        COALESCE(SUM(m.quantity * p.purchase_price) FILTER (WHERE m.movement_type = 'breakage'), 0) AS breakage_cost,
        COUNT(*) FILTER (WHERE m.movement_type = 'purchase') AS purchase_transactions,
        COALESCE(SUM(m.quantity) FILTER (WHERE m.movement_type = 'purchase'), 0) AS qty_purchased,
        COALESCE(SUM(m.quantity * m.unit_purchase_price) FILTER (WHERE m.movement_type = 'purchase'), 0) AS purchase_cost,
        COUNT(*) AS total_movements
    FROM core.movements m JOIN core.products p ON p.product_id = m.product_id
    GROUP BY m.store_id, m.movement_date
    """)
