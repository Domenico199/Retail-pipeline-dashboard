CREATE TABLE IF NOT EXISTS staging.cleaned_movements (
    cleaned_movement_id      BIGSERIAL PRIMARY KEY,

    raw_movement_id          BIGINT NOT NULL UNIQUE,
    source_file_name         VARCHAR(255) NOT NULL,
    source_system            VARCHAR(50) NOT NULL DEFAULT 'simulated_api',

    store_id                 INTEGER NOT NULL,
    product_id               VARCHAR(50) NOT NULL,
    supplier_id              VARCHAR(20),

    movement_type            VARCHAR(20) NOT NULL CHECK (
        movement_type IN ('sale', 'purchase', 'breakage')
    ),

    quantity                 INTEGER NOT NULL CHECK (quantity > 0),

    unit_sale_price          NUMERIC(12,4),
    unit_purchase_price      NUMERIC(12,4),
    is_promo                 BOOLEAN NOT NULL DEFAULT FALSE,
    promo_type               VARCHAR(50),

    movement_timestamp       TIMESTAMP NOT NULL,
    movement_date            DATE NOT NULL,

    loaded                   BOOLEAN NOT NULL DEFAULT FALSE,
    cleaned_at               TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    loaded_at                TIMESTAMP,

    CONSTRAINT fk_cleaned_raw_movement
        FOREIGN KEY (raw_movement_id)
        REFERENCES staging.raw_movements(raw_movement_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_cleaned_product
        FOREIGN KEY (product_id)
        REFERENCES core.products(product_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_cleaned_supplier
        FOREIGN KEY (supplier_id)
        REFERENCES core.suppliers(supplier_id)
        ON DELETE SET NULL,

    CONSTRAINT chk_cleaned_sale_price
        CHECK (
            (movement_type <> 'sale')
            OR (unit_sale_price IS NOT NULL AND unit_sale_price > 0)
        ),

    CONSTRAINT chk_cleaned_purchase_price
        CHECK (
            (movement_type <> 'purchase')
            OR (unit_purchase_price IS NOT NULL AND unit_purchase_price > 0)
        ),

    CONSTRAINT chk_cleaned_breakage_prices
        CHECK (
            (movement_type <> 'breakage')
            OR (unit_sale_price IS NULL AND unit_purchase_price IS NULL)
        )
);

CREATE INDEX IF NOT EXISTS idx_cleaned_movements_loaded
    ON staging.cleaned_movements(loaded);

CREATE INDEX IF NOT EXISTS idx_cleaned_movements_date
    ON staging.cleaned_movements(movement_date);

CREATE INDEX IF NOT EXISTS idx_cleaned_movements_product
    ON staging.cleaned_movements(product_id);

CREATE INDEX IF NOT EXISTS idx_cleaned_movements_file
    ON staging.cleaned_movements(source_file_name);



CREATE TABLE IF NOT EXISTS staging.bad_movements (
    bad_movement_id          BIGSERIAL PRIMARY KEY,

    raw_movement_id          BIGINT NOT NULL UNIQUE,
    source_file_name         VARCHAR(255) NOT NULL,
    source_system            VARCHAR(50) NOT NULL DEFAULT 'simulated_api',

    store_id                 INTEGER,
    product_id               VARCHAR(50),
    supplier_id              VARCHAR(20),

    movement_type            VARCHAR(20),
    quantity                 INTEGER,

    unit_sale_price          NUMERIC(12,4),
    unit_purchase_price      NUMERIC(12,4),
    is_promo                 BOOLEAN,
    promo_type               VARCHAR(50),

    movement_timestamp       TIMESTAMP,
    movement_date            DATE,

    error_reason             VARCHAR(255) NOT NULL,
    error_details            TEXT,
    rejected_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    reviewed                 BOOLEAN NOT NULL DEFAULT FALSE,
    corrected                BOOLEAN NOT NULL DEFAULT FALSE,
    correction_notes         TEXT,

    CONSTRAINT fk_bad_raw_movement
        FOREIGN KEY (raw_movement_id)
        REFERENCES staging.raw_movements(raw_movement_id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_bad_movements_reason
    ON staging.bad_movements(error_reason);

CREATE INDEX IF NOT EXISTS idx_bad_movements_reviewed
    ON staging.bad_movements(reviewed);

CREATE INDEX IF NOT EXISTS idx_bad_movements_corrected
    ON staging.bad_movements(corrected);

CREATE INDEX IF NOT EXISTS idx_bad_movements_file
    ON staging.bad_movements(source_file_name);