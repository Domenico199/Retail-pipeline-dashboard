import pandas as pd
from dotenv import load_dotenv
from src.db import get_db_engine


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
def validate(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    """
    Apply business validation rules on top of what the DB constraints already enforce.
    Returns (df_clean, df_bad).

    Rows already in raw_movements passed structural DB constraints (FK, price CHECKs).
    This step catches remaining business logic errors.
    """
    bad_mask = pd.Series(False, index=df.index)
    error_reason = pd.Series("", index=df.index)
    error_details = pd.Series("", index=df.index)

    # Rule: purchase without supplier
    purchase_no_supplier = (df["movement_type"] == "purchase") & df["supplier_id"].isna()
    bad_mask |= purchase_no_supplier
    error_reason[purchase_no_supplier] = "purchase_without_supplier"
    error_details[purchase_no_supplier] = "movement_type='purchase' but supplier_id is NULL"

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

    print(f"Found {len(files)} file(s) to transform.")

    for file_name in files:
        try:
            df = load_raw_for_file(file_name, engine)
            df_clean, df_bad = validate(df)

            if not df_clean.empty:
                load_cleaned(df_clean, engine)
            if not df_bad.empty:
                load_bad(df_bad, engine)

            print(
                f"  ✓ {file_name}: "
                f"{len(df_clean)} cleaned | {len(df_bad)} bad"
            )
        except Exception as e:
            print(f"  ✗ {file_name}: failed — {e}")

    print("Done.")


if __name__ == "__main__":
    main()
