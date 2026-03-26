CREATE TABLE IF NOT EXISTS sim.products_specifications (
    product_id                  VARCHAR(50) PRIMARY KEY,
    rotation_class              VARCHAR(20) NOT NULL CHECK (rotation_class IN ('high', 'medium', 'low')),
    spoilage_probability        NUMERIC(6,5) NOT NULL CHECK (spoilage_probability >= 0 AND spoilage_probability <= 1),
    initial_stock               INTEGER NOT NULL CHECK (initial_stock >= 0),
    minimum_stock_threshold     INTEGER NOT NULL CHECK (minimum_stock_threshold >= 0),
    reorder_lot                 INTEGER NOT NULL CHECK (reorder_lot >= 0),
    assortment_flag             BOOLEAN DEFAULT TRUE,
    created_at                  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at                  TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT fk_sim_product
        FOREIGN KEY (product_id)
        REFERENCES core.products(product_id)
        ON DELETE CASCADE
);