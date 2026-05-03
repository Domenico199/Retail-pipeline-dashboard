"""add_brand_name_to_analytics_views

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-04-08 11:00:00.000000

Aggiunge brand_name (da core.brands) alle view che usano brand_code:
- shelf_movements_current
- shelf_detail
- margins_by_product_shelf
"""
from typing import Sequence, Union

from alembic import op

revision: str = 'f6a7b8c9d0e1'
down_revision: Union[str, None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Crea tabella core.brands
    op.execute("""
    CREATE TABLE IF NOT EXISTS core.brands (
        brand_code  VARCHAR(20) PRIMARY KEY,
        brand_name  VARCHAR(100) NOT NULL,
        created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """)

    # shelf_movements_current: aggiunge brand_name
    op.execute("DROP VIEW IF EXISTS analytics.shelf_movements_current")
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
        p.brand_code,
        b.brand_name,
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
    LEFT JOIN core.brands b ON b.brand_code = p.brand_code
    """)

    # shelf_detail: aggiunge brand_name
    op.execute("DROP VIEW IF EXISTS analytics.shelf_detail")
    op.execute("""
    CREATE VIEW analytics.shelf_detail AS
    SELECT
        sl.store_id,
        sl.shelf_id,
        sl.shelf_category,
        sl.shelf_level,
        sl.zone,
        sl.slot_number,
        sl.capacity,
        sa.product_id,
        sa.active_flag,
        p.product_description,
        p.category_level_1,
        p.category_level_2,
        p.brand_code,
        b.brand_name
    FROM core.store_layout sl
    LEFT JOIN core.store_assortment sa
        ON sa.store_id = sl.store_id
       AND sa.shelf_id = sl.shelf_id
       AND sa.shelf_level = sl.shelf_level
       AND sa.zone = sl.zone
       AND sa.slot_number = sl.slot_number
    LEFT JOIN core.products p ON p.product_id = sa.product_id
    LEFT JOIN core.brands b ON b.brand_code = p.brand_code
    """)

    # margins_by_product_shelf: aggiunge brand_name
    op.execute("DROP VIEW IF EXISTS analytics.margins_by_product_shelf")
    op.execute("""
    CREATE VIEW analytics.margins_by_product_shelf AS
    SELECT
        m.store_id,
        m.product_id,
        p.product_description,
        p.category_level_1,
        p.category_level_2,
        p.brand_code,
        b.brand_name,
        m.shelf_id,
        m.movement_date,
        TO_CHAR(m.movement_date, 'YYYY-MM')              AS month,
        EXTRACT(YEAR FROM m.movement_date)::INTEGER       AS year,
        EXTRACT(WEEK FROM m.movement_date)::INTEGER       AS week,
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
    LEFT JOIN core.brands b ON b.brand_code = p.brand_code
    WHERE m.movement_type = 'sale'
    GROUP BY m.store_id, m.product_id, p.product_description,
             p.category_level_1, p.category_level_2,
             p.brand_code, b.brand_name,
             m.shelf_id, m.movement_date
    """)


def downgrade() -> None:
    # Ripristina le view senza brand_name
    op.execute("DROP VIEW IF EXISTS analytics.shelf_movements_current")
    op.execute("""
    CREATE VIEW analytics.shelf_movements_current AS
    SELECT
        sa.store_id, sa.shelf_id, sa.shelf_level, sa.zone, sa.slot_number,
        m.product_id, p.product_description, p.category_level_1, p.category_level_2, p.brand_code,
        m.movement_type, m.quantity, m.unit_sale_price, m.unit_purchase_price,
        p.purchase_price AS unit_cost, m.is_promo, m.movement_date,
        TO_CHAR(m.movement_date, 'YYYY-MM') AS month,
        EXTRACT(YEAR FROM m.movement_date)::INTEGER AS year,
        EXTRACT(WEEK FROM m.movement_date)::INTEGER AS week
    FROM core.movements m
    JOIN core.store_assortment sa ON sa.store_id = m.store_id AND sa.product_id = m.product_id AND sa.active_flag = TRUE
    JOIN core.products p ON p.product_id = m.product_id
    """)

    op.execute("DROP VIEW IF EXISTS analytics.shelf_detail")
    op.execute("""
    CREATE VIEW analytics.shelf_detail AS
    SELECT sl.store_id, sl.shelf_id, sl.shelf_category, sl.shelf_level, sl.zone, sl.slot_number, sl.capacity,
        sa.product_id, sa.active_flag, p.product_description, p.category_level_1, p.category_level_2, p.brand_code
    FROM core.store_layout sl
    LEFT JOIN core.store_assortment sa ON sa.store_id = sl.store_id AND sa.shelf_id = sl.shelf_id
        AND sa.shelf_level = sl.shelf_level AND sa.zone = sl.zone AND sa.slot_number = sl.slot_number
    LEFT JOIN core.products p ON p.product_id = sa.product_id
    """)

    op.execute("DROP VIEW IF EXISTS analytics.margins_by_product_shelf")
    op.execute("""
    CREATE VIEW analytics.margins_by_product_shelf AS
    SELECT m.store_id, m.product_id, p.product_description, p.category_level_1, p.category_level_2, p.brand_code,
        m.shelf_id, m.movement_date,
        TO_CHAR(m.movement_date, 'YYYY-MM') AS month,
        EXTRACT(YEAR FROM m.movement_date)::INTEGER AS year,
        EXTRACT(WEEK FROM m.movement_date)::INTEGER AS week,
        SUM(m.quantity) AS qty_sold, SUM(m.quantity * m.unit_sale_price) AS revenue,
        SUM(m.quantity * p.purchase_price) AS cost,
        SUM(m.quantity * m.unit_sale_price) - SUM(m.quantity * p.purchase_price) AS margin,
        CASE WHEN SUM(m.quantity * m.unit_sale_price) = 0 THEN 0
            ELSE ROUND((SUM(m.quantity * m.unit_sale_price) - SUM(m.quantity * p.purchase_price))
            / SUM(m.quantity * m.unit_sale_price) * 100, 2) END AS margin_pct
    FROM core.movements m JOIN core.products p ON p.product_id = m.product_id
    WHERE m.movement_type = 'sale'
    GROUP BY m.store_id, m.product_id, p.product_description, p.category_level_1, p.category_level_2,
             p.brand_code, m.shelf_id, m.movement_date
    """)

    op.execute("DROP TABLE IF EXISTS core.brands")
