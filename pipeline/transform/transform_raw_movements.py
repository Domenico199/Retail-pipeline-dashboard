import pandas as pd
from dotenv import load_dotenv
from src.db import get_db_engine
from pipeline.run_tracker import RunTracker


load_dotenv()


# GET FILES WITH RAW DATA NOT YET TRANSFORMED
def get_files_to_transform(engine) -> list[str]:
    """
    Returns file names that have rows in raw_movements but have not yet been
    processed into cleaned_movements or bad_movements.
    """
    query = """
        SELECT DISTINCT source_file_name FROM staging.raw_movements
        EXCEPT (
            SELECT DISTINCT source_file_name FROM staging.cleaned_movements
            UNION
            SELECT DISTINCT source_file_name FROM staging.bad_movements
        )
    """
    df = pd.read_sql(query, engine)
    return sorted(df["source_file_name"].tolist())


# LOAD RAW MOVEMENTS FOR A SPECIFIC FILE
def load_raw_for_file(file_name: str, engine) -> pd.DataFrame:
    """Load all raw_movements rows for the given source file."""
    query = """
        SELECT * FROM staging.raw_movements
        WHERE source_file_name = %(file_name)s
    """
    return pd.read_sql(query, engine, params={"file_name": file_name})


# VALIDATE: SPLIT INTO CLEAN AND BAD
def validate(df: pd.DataFrame, valid_products: set, valid_suppliers: set) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Apply all validation rules — structural and business logic.
    Returns (df_clean, df_bad).

    Since raw_movements no longer has FK/CHECK constraints,
    ALL validation happens here.
    """
    bad_mask = pd.Series(False, index=df.index)
    error_reason = pd.Series("", index=df.index)
    error_details = pd.Series("", index=df.index)

    def apply_rule(mask, reason, details):
        """Apply a validation rule: only mark rows not already flagged."""
        nonlocal bad_mask, error_reason, error_details
        new_bad = mask & ~bad_mask  # only flag rows not already bad
        bad_mask |= mask
        error_reason[new_bad] = reason
        error_details[new_bad] = details

    # 1. Unknown product
    unknown_product = ~df["product_id"].isin(valid_products)
    apply_rule(unknown_product, "unknown_product", "product_id not found in core.products")

    # 2. Unknown supplier (only when supplier_id is not null)
    has_supplier = df["supplier_id"].notna()
    unknown_supplier = has_supplier & ~df["supplier_id"].isin(valid_suppliers)
    apply_rule(unknown_supplier, "unknown_supplier", "supplier_id not found in core.suppliers")

    # 3. Sale without price
    sale_no_price = (df["movement_type"] == "sale") & (
        df["unit_sale_price"].isna() | (df["unit_sale_price"] <= 0)
    )
    apply_rule(sale_no_price, "missing_sale_price", "movement_type='sale' but unit_sale_price is missing or <= 0")

    # 4. Purchase without price
    purchase_no_price = (df["movement_type"] == "purchase") & (
        df["unit_purchase_price"].isna() | (df["unit_purchase_price"] <= 0)
    )
    apply_rule(purchase_no_price, "missing_purchase_price", "movement_type='purchase' but unit_purchase_price is missing or <= 0")

    # 5. Breakage with price (should be NULL)
    breakage_with_price = (df["movement_type"] == "breakage") & (
        df["unit_sale_price"].notna() | df["unit_purchase_price"].notna()
    )
    apply_rule(breakage_with_price, "breakage_with_price", "movement_type='breakage' but prices are not NULL")

    # 6. Purchase without supplier
    purchase_no_supplier = (df["movement_type"] == "purchase") & df["supplier_id"].isna()
    apply_rule(purchase_no_supplier, "purchase_without_supplier", "movement_type='purchase' but supplier_id is NULL")

    df_bad = df[bad_mask].copy()
    df_bad["error_reason"] = error_reason[bad_mask].values
    df_bad["error_details"] = error_details[bad_mask].values

    df_clean = df[~bad_mask].copy()

    return df_clean, df_bad


# LOAD CLEANED MOVEMENTS
def load_cleaned(df_clean: pd.DataFrame, engine):
    """Insert validated rows into staging.cleaned_movements."""
    cols = [
        "raw_movement_id", "source_file_name", "source_system",
        "store_id", "product_id", "supplier_id",
        "movement_type", "quantity",
        "unit_sale_price", "unit_purchase_price",
        "is_promo", "promo_type",
        "movement_timestamp", "movement_date",
    ]
    df_clean[cols].to_sql(
        name="cleaned_movements",
        con=engine,
        schema="staging",
        if_exists="append",
        index=False,
    )


# LOAD BAD MOVEMENTS
def load_bad(df_bad: pd.DataFrame, engine):
    """Insert rejected rows into staging.bad_movements."""
    cols = [
        "raw_movement_id", "source_file_name", "source_system",
        "store_id", "product_id", "supplier_id",
        "movement_type", "quantity",
        "unit_sale_price", "unit_purchase_price",
        "is_promo", "promo_type",
        "movement_timestamp", "movement_date",
        "error_reason", "error_details",
    ]
    df_bad[cols].to_sql(
        name="bad_movements",
        con=engine,
        schema="staging",
        if_exists="append",
        index=False,
    )


# MAIN
def main():
    """Main function to transform raw movements into cleaned and bad."""
    engine = get_db_engine()
    files = get_files_to_transform(engine)

    if not files:
        print("No files to transform.")
        return

    # Load valid reference sets once (used for all files)
    valid_products = set(pd.read_sql("SELECT product_id FROM core.products", engine)["product_id"])
    valid_suppliers = set(pd.read_sql("SELECT supplier_id FROM core.suppliers", engine)["supplier_id"])

    print(f"Found {len(files)} file(s) to transform.")

    for file_name in files:
        tracker = RunTracker(engine, "transform")
        tracker.start(source_file_name=file_name)
        try:
            df = load_raw_for_file(file_name, engine)
            df_clean, df_bad = validate(df, valid_products, valid_suppliers)

            if not df_clean.empty:
                load_cleaned(df_clean, engine)
            if not df_bad.empty:
                load_bad(df_bad, engine)

            tracker.complete(
                rows_processed=len(df),
                rows_success=len(df_clean),
                rows_failed=len(df_bad),
            )
            print(
                f"  ✓ {file_name}: "
                f"{len(df_clean)} cleaned | {len(df_bad)} bad"
            )
        except Exception as e:
            tracker.fail(str(e))
            print(f"  ✗ {file_name}: failed — {e}")

    print("Done.")


if __name__ == "__main__":
    main()
