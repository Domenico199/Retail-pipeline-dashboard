CREATE TABLE IF NOT EXISTS core.products (
    product_id              VARCHAR(50) PRIMARY KEY,
    product_description     TEXT NOT NULL,
    category_level_1        VARCHAR(100),
    category_level_2        VARCHAR(100),
    category_level_3        VARCHAR(100),
    vat_rate                NUMERIC(5,2),
    unit_of_measure         VARCHAR(20),
    purchase_price          NUMERIC(12,4),
    sale_price              NUMERIC(12,4),
    brand_code              VARCHAR(20),
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_core_products_cat1
    ON core.products(category_level_1);

CREATE INDEX IF NOT EXISTS idx_core_products_cat2
    ON core.products(category_level_2);

CREATE INDEX IF NOT EXISTS idx_core_products_cat3
    ON core.products(category_level_3);

CREATE INDEX IF NOT EXISTS idx_core_products_brand
    ON core.products(brand_code);



CREATE TABLE IF NOT EXISTS core.store_layout (
    store_id              INTEGER NOT NULL,
    shelf_id              INTEGER NOT NULL,
    shelf_category        VARCHAR(100),

    shelf_level           INTEGER NOT NULL CHECK (shelf_level BETWEEN 1 AND 5),
    zone                  VARCHAR(10) NOT NULL CHECK (zone IN ('left', 'center', 'right')),
    slot_number           INTEGER NOT NULL CHECK (slot_number BETWEEN 1 AND 3),

    capacity              INTEGER DEFAULT 1 CHECK (capacity > 0),

    created_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_store_layout PRIMARY KEY (
        store_id,
        shelf_id,
        shelf_level,
        zone,
        slot_number
    )
);



CREATE TABLE IF NOT EXISTS core.store_assortment (
    store_id              INTEGER NOT NULL,
    product_id            VARCHAR(50) NOT NULL,

    shelf_id              INTEGER NOT NULL,
    shelf_level           INTEGER NOT NULL,
    zone                  VARCHAR(10) NOT NULL,
    slot_number           INTEGER NOT NULL,

    active_flag           BOOLEAN DEFAULT TRUE,

    created_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_store_assortment PRIMARY KEY (
        store_id,
        product_id
    ),

    CONSTRAINT uq_store_position UNIQUE (
        store_id,
        shelf_id,
        shelf_level,
        zone,
        slot_number
    ),

    CONSTRAINT fk_assortment_product
        FOREIGN KEY (product_id)
        REFERENCES core.products(product_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_assortment_layout
        FOREIGN KEY (store_id, shelf_id, shelf_level, zone, slot_number)
        REFERENCES core.store_layout(store_id, shelf_id, shelf_level, zone, slot_number)
        ON DELETE CASCADE
);



CREATE TABLE IF NOT EXISTS core.inventory (
    store_id              INTEGER NOT NULL,
    product_id            VARCHAR(50) NOT NULL,

    stock_qty             INTEGER NOT NULL CHECK (stock_qty >= 0),

    created_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_inventory PRIMARY KEY (
        store_id,
        product_id
    ),

    CONSTRAINT fk_inventory_product
        FOREIGN KEY (product_id)
        REFERENCES core.products(product_id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_inventory_product
    ON core.inventory(product_id);



CREATE TABLE IF NOT EXISTS core.suppliers (
    supplier_id           VARCHAR(20) PRIMARY KEY,
    supplier_name         VARCHAR(100) NOT NULL UNIQUE,
    supplier_type         VARCHAR(20) NOT NULL CHECK (
        supplier_type IN ('primary', 'secondary')
    ),

    created_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_suppliers_type
    ON core.suppliers(supplier_type);



CREATE TABLE IF NOT EXISTS core.product_suppliers (
    product_id            VARCHAR(50) NOT NULL,
    supplier_id           VARCHAR(20) NOT NULL,

    is_primary_supplier   BOOLEAN NOT NULL DEFAULT FALSE,

    created_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at            TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    CONSTRAINT pk_product_suppliers PRIMARY KEY (
        product_id,
        supplier_id
    ),

    CONSTRAINT fk_product_suppliers_product
        FOREIGN KEY (product_id)
        REFERENCES core.products(product_id)
        ON DELETE CASCADE,

    CONSTRAINT fk_product_suppliers_supplier
        FOREIGN KEY (supplier_id)
        REFERENCES core.suppliers(supplier_id)
        ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_product_suppliers_product
    ON core.product_suppliers(product_id);

CREATE INDEX IF NOT EXISTS idx_product_suppliers_supplier
    ON core.product_suppliers(supplier_id);

CREATE INDEX IF NOT EXISTS idx_product_suppliers_primary
    ON core.product_suppliers(is_primary_supplier);



