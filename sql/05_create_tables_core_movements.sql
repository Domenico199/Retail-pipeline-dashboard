CREATE TABLE IF NOT EXISTS core.movements (
    movement_id           BIGSERIAL PRIMARY KEY,

    raw_movement_id       BIGINT UNIQUE,
    source_file_name      VARCHAR(255) NOT NULL,
    source_system         VARCHAR(50) NOT NULL DEFAULT 'simulated_api',

    store_id              INTEGER NOT NULL,
    product_id            VARCHAR(50) NOT NULL,
    supplier_id           VARCHAR(20),

    shelf_id              INTEGER,
    shelf_level           INTEGER,
    zone                  VARCHAR(10),
    slot_number           INTEGER,

    movement_type         VARCHAR(20) NOT NULL CHECK (
        movement_type IN ('sale', 'purchase', 'breakage')
    ),

    quantity              INTEGER NOT NULL CHECK (quantity > 0),

    unit_sale_price       NUMERIC(12,4),
    unit_purchase_price   NUMERIC(12,4),
    is_promo              BOOLEAN NOT NULL DEFAULT FALSE,
    promo_type            VARCHAR(50),

    movement_timestamp    TIMESTAMP NOT NULL,
    movement_date         DATE NOT NULL,

    created_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT fk_core_movements_product
        FOREIGN KEY (product_id)
        REFERENCES core.products(product_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_core_movements_supplier
        FOREIGN KEY (supplier_id)
        REFERENCES core.suppliers(supplier_id)
        ON DELETE SET NULL,

    CONSTRAINT fk_core_movements_raw
        FOREIGN KEY (raw_movement_id)
        REFERENCES staging.raw_movements(raw_movement_id)
        ON DELETE SET NULL,

    CONSTRAINT chk_core_movements_sale_price
        CHECK (
            (movement_type <> 'sale')
            OR (unit_sale_price IS NOT NULL AND unit_sale_price > 0)
        ),

    CONSTRAINT chk_core_movements_purchase_price
        CHECK (
            (movement_type <> 'purchase')
            OR (unit_purchase_price IS NOT NULL AND unit_purchase_price > 0)
        ),

    CONSTRAINT chk_core_movements_breakage_prices
        CHECK (
            (movement_type <> 'breakage')
            OR (unit_sale_price IS NULL AND unit_purchase_price IS NULL)
        )
);

CREATE INDEX IF NOT EXISTS idx_core_movements_date
    ON core.movements(movement_date);

CREATE INDEX IF NOT EXISTS idx_core_movements_timestamp
    ON core.movements(movement_timestamp);

CREATE INDEX IF NOT EXISTS idx_core_movements_type
    ON core.movements(movement_type);

CREATE INDEX IF NOT EXISTS idx_core_movements_product
    ON core.movements(product_id);

CREATE INDEX IF NOT EXISTS idx_core_movements_supplier
    ON core.movements(supplier_id);

CREATE INDEX IF NOT EXISTS idx_core_movements_store
    ON core.movements(store_id);

CREATE INDEX IF NOT EXISTS idx_core_movements_file
    ON core.movements(source_file_name);

CREATE INDEX IF NOT EXISTS idx_core_movements_shelf
    ON core.movements(store_id, shelf_id, shelf_level, zone, slot_number);