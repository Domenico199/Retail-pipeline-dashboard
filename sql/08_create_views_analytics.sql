-- ============================================================
-- Analytics layer: views per Power BI
-- ============================================================

CREATE SCHEMA IF NOT EXISTS analytics;

-- 1. Vendite per scaffale (storico: posizione al momento della vendita)
CREATE OR REPLACE VIEW analytics.sales_by_shelf_historical AS
SELECT
    m.store_id,
    m.shelf_id,
    m.movement_date,
    TO_CHAR(m.movement_date, 'YYYY-MM')              AS month,
    EXTRACT(YEAR FROM m.movement_date)::INTEGER       AS year,
    EXTRACT(WEEK FROM m.movement_date)::INTEGER       AS week,
    COUNT(*)            AS transaction_count,
    SUM(m.quantity)     AS qty_sold,
    SUM(m.quantity * m.unit_sale_price) AS revenue
FROM core.movements m
WHERE m.movement_type = 'sale'
  AND m.shelf_id IS NOT NULL
GROUP BY m.store_id, m.shelf_id, m.movement_date;


-- 2. Vendite per scaffale (corrente: posizione attuale del prodotto)
CREATE OR REPLACE VIEW analytics.sales_by_shelf_current AS
SELECT
    m.store_id,
    sa.shelf_id,
    m.movement_date,
    TO_CHAR(m.movement_date, 'YYYY-MM')              AS month,
    EXTRACT(YEAR FROM m.movement_date)::INTEGER       AS year,
    EXTRACT(WEEK FROM m.movement_date)::INTEGER       AS week,
    COUNT(*)            AS transaction_count,
    SUM(m.quantity)     AS qty_sold,
    SUM(m.quantity * m.unit_sale_price) AS revenue
FROM core.movements m
JOIN core.store_assortment sa
    ON sa.store_id = m.store_id
   AND sa.product_id = m.product_id
   AND sa.active_flag = TRUE
WHERE m.movement_type = 'sale'
GROUP BY m.store_id, sa.shelf_id, m.movement_date;


-- 3. Rotture per scaffale (storico)
CREATE OR REPLACE VIEW analytics.breakage_by_shelf_historical AS
SELECT
    m.store_id,
    m.shelf_id,
    m.movement_date,
    TO_CHAR(m.movement_date, 'YYYY-MM')              AS month,
    EXTRACT(YEAR FROM m.movement_date)::INTEGER       AS year,
    EXTRACT(WEEK FROM m.movement_date)::INTEGER       AS week,
    COUNT(*)            AS breakage_events,
    SUM(m.quantity)     AS qty_lost,
    SUM(m.quantity * p.purchase_price) AS breakage_cost
FROM core.movements m
JOIN core.products p ON p.product_id = m.product_id
WHERE m.movement_type = 'breakage'
  AND m.shelf_id IS NOT NULL
GROUP BY m.store_id, m.shelf_id, m.movement_date;


-- 4. Rotture per scaffale (corrente)
CREATE OR REPLACE VIEW analytics.breakage_by_shelf_current AS
SELECT
    m.store_id,
    sa.shelf_id,
    m.movement_date,
    TO_CHAR(m.movement_date, 'YYYY-MM')              AS month,
    EXTRACT(YEAR FROM m.movement_date)::INTEGER       AS year,
    EXTRACT(WEEK FROM m.movement_date)::INTEGER       AS week,
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
GROUP BY m.store_id, sa.shelf_id, m.movement_date;


-- 5. Margini per prodotto e scaffale
CREATE OR REPLACE VIEW analytics.margins_by_product_shelf AS
SELECT
    m.store_id,
    m.product_id,
    p.product_description,
    p.category_level_1,
    p.category_level_2,
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
WHERE m.movement_type = 'sale'
GROUP BY m.store_id, m.product_id, p.product_description,
         p.category_level_1, p.category_level_2,
         m.shelf_id, m.movement_date;


-- 6. KPI giornalieri
CREATE OR REPLACE VIEW analytics.daily_kpis AS
SELECT
    m.store_id,
    m.movement_date,
    TO_CHAR(m.movement_date, 'YYYY-MM')              AS month,
    EXTRACT(YEAR FROM m.movement_date)::INTEGER       AS year,
    EXTRACT(WEEK FROM m.movement_date)::INTEGER       AS week,
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
GROUP BY m.store_id, m.movement_date;


-- 7. Inventario per scaffale (stato attuale)
CREATE OR REPLACE VIEW analytics.inventory_by_shelf AS
SELECT
    sa.store_id,
    sa.shelf_id,
    sa.shelf_level,
    sa.zone,
    sa.slot_number,
    sa.product_id,
    p.product_description,
    p.category_level_1,
    i.stock_qty,
    sl.capacity,
    CASE
        WHEN sl.capacity = 0 THEN 0
        ELSE ROUND(i.stock_qty::NUMERIC / sl.capacity * 100, 1)
    END AS fill_pct
FROM core.store_assortment sa
JOIN core.products p ON p.product_id = sa.product_id
JOIN core.inventory i
    ON i.store_id = sa.store_id
   AND i.product_id = sa.product_id
JOIN core.store_layout sl
    ON sl.store_id = sa.store_id
   AND sl.shelf_id = sa.shelf_id
   AND sl.shelf_level = sa.shelf_level
   AND sl.zone = sa.zone
   AND sl.slot_number = sa.slot_number
WHERE sa.active_flag = TRUE;


-- 8. Dettaglio scaffale (dimensione per Power BI)
CREATE OR REPLACE VIEW analytics.shelf_detail AS
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
    p.brand_code
FROM core.store_layout sl
LEFT JOIN core.store_assortment sa
    ON sa.store_id = sl.store_id
   AND sa.shelf_id = sl.shelf_id
   AND sa.shelf_level = sl.shelf_level
   AND sa.zone = sl.zone
   AND sa.slot_number = sl.slot_number
LEFT JOIN core.products p
    ON p.product_id = sa.product_id;


-- 9. Movimenti per posizione attuale (non aggregata, per dashboard scaffale)
CREATE OR REPLACE VIEW analytics.shelf_movements_current AS
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
JOIN core.products p ON p.product_id = m.product_id;
