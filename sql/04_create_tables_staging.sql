CREATE TABLE IF NOT EXISTS staging.raw_movements (
    raw_movement_id       BIGSERIAL PRIMARY KEY,

    source_file_name      VARCHAR(255) NOT NULL,
    source_system         VARCHAR(50) NOT NULL DEFAULT 'simulated_api',

    store_id              INTEGER NOT NULL,
    product_id            VARCHAR(50) NOT NULL,
    supplier_id           VARCHAR(20),

    movement_type         VARCHAR(20) NOT NULL CHECK (
        movement_type IN ('sale', 'purchase', 'breakage')
    ),

    quantity              INTEGER NOT NULL CHECK (quantity > 0),

    unit_sale_price      NUMERIC(12,4),
    unit_purchase_price  NUMERIC(12,4),
    is_promo             BOOLEAN NOT NULL DEFAULT FALSE,
    promo_type           VARCHAR(50),

    movement_timestamp    TIMESTAMP NOT NULL,
    movement_date         DATE NOT NULL,

    ingestion_timestamp   TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_raw_movements_product
        FOREIGN KEY (product_id)
        REFERENCES core.products(product_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_raw_movements_supplier
        FOREIGN KEY (supplier_id)
        REFERENCES core.suppliers(supplier_id)
        ON DELETE SET NULL,

    CONSTRAINT chk_raw_movements_sale_price
        CHECK (
            (movement_type <> 'sale')
            OR (unit_sale_price IS NOT NULL AND unit_sale_price > 0)
        ),

    CONSTRAINT chk_raw_movements_purchase_price
        CHECK (
            (movement_type <> 'purchase')
            OR (unit_purchase_price IS NOT NULL AND unit_purchase_price > 0)
        ),

    CONSTRAINT chk_raw_movements_breakage_prices
        CHECK (
            (movement_type <> 'breakage')
            OR (unit_sale_price IS NULL AND unit_purchase_price IS NULL)
        )
);

CREATE INDEX IF NOT EXISTS idx_raw_movements_date
    ON staging.raw_movements(movement_date);

CREATE INDEX IF NOT EXISTS idx_raw_movements_type
    ON staging.raw_movements(movement_type);

CREATE INDEX IF NOT EXISTS idx_raw_movements_product
    ON staging.raw_movements(product_id);

CREATE INDEX IF NOT EXISTS idx_raw_movements_supplier
    ON staging.raw_movements(supplier_id);

CREATE INDEX IF NOT EXISTS idx_raw_movements_file
    ON staging.raw_movements(source_file_name);


CREATE TABLE IF NOT EXISTS staging.processed_files (
    file_name             VARCHAR(255) PRIMARY KEY,
    source_system         VARCHAR(50) NOT NULL DEFAULT 'simulated_api',
    processed_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);