import pandas as pd
from sqlalchemy import text
from dotenv import load_dotenv
from src.db import get_db_engine
from pipeline.run_tracker import RunTracker


load_dotenv()


# GET UNLOADED MOVEMENTS FROM CLEANED
def get_unloaded_movements(engine) -> pd.DataFrame:
    """Read all cleaned movements not yet loaded into core."""
    query = """
        SELECT * FROM staging.cleaned_movements
        WHERE loaded = FALSE
    """
    return pd.read_sql(query, engine)


# ENRICH WITH SHELF POSITION
def enrich_with_shelf_position(df: pd.DataFrame, engine) -> pd.DataFrame:
    """LEFT JOIN with core.store_assortment to capture current shelf position."""
    assortment = pd.read_sql("""
        SELECT product_id, shelf_id, shelf_level, zone, slot_number
        FROM core.store_assortment
        WHERE store_id = 1 AND active_flag = TRUE
    """, engine)

    df = df.merge(assortment, on="product_id", how="left")
    return df


# INSERT INTO CORE.MOVEMENTS
def insert_to_core_movements(df: pd.DataFrame, conn):
    """Insert enriched movements into core.movements."""
    cols = [
        "raw_movement_id", "source_file_name", "source_system",
        "store_id", "product_id", "supplier_id",
        "shelf_id", "shelf_level", "zone", "slot_number",
        "movement_type", "quantity",
        "unit_sale_price", "unit_purchase_price",
        "is_promo", "promo_type",
        "movement_timestamp", "movement_date",
    ]
    df[cols].to_sql(
        name="movements",
        con=conn,
        schema="core",
        if_exists="append",
        index=False,
    )


# UPDATE INVENTORY
def update_inventory(df: pd.DataFrame, conn):
    """
    Update core.inventory with net stock changes.
    sale/breakage → subtract, purchase → add.
    """
    delta = df.groupby(["store_id", "product_id"]).apply(
        lambda g: g.apply(
            lambda r: r["quantity"] if r["movement_type"] == "purchase" else -r["quantity"],
            axis=1
        ).sum()
    ).reset_index(name="net_qty")

    for _, row in delta.iterrows():
        conn.execute(
            text("""
                UPDATE core.inventory
                SET stock_qty = stock_qty + :net_qty
                WHERE store_id = :store_id
                  AND product_id = :product_id
            """),
            {
                "net_qty": int(row["net_qty"]),
                "store_id": int(row["store_id"]),
                "product_id": row["product_id"],
            },
        )


# MARK AS LOADED
def mark_as_loaded(cleaned_ids: list, conn):
    """Set loaded=TRUE and loaded_at=NOW() for processed cleaned movements."""
    conn.execute(
        text("""
            UPDATE staging.cleaned_movements
            SET loaded = TRUE,
                loaded_at = CURRENT_TIMESTAMP
            WHERE cleaned_movement_id = ANY(:ids)
        """),
        {"ids": cleaned_ids},
    )


# MAIN
def main():
    """Load cleaned movements into core.movements and update inventory."""
    engine = get_db_engine()

    df = get_unloaded_movements(engine)

    if df.empty:
        print("Nothing to load.")
        return

    n_rows = len(df)
    print(f"Found {n_rows} movements to load.")

    tracker = RunTracker(engine, "load")
    tracker.start()

    try:
        cleaned_ids = df["cleaned_movement_id"].tolist()

        df = enrich_with_shelf_position(df, engine)

        with engine.begin() as conn:
            insert_to_core_movements(df, conn)
            update_inventory(df, conn)
            mark_as_loaded(cleaned_ids, conn)

        tracker.complete(rows_processed=n_rows, rows_success=n_rows, rows_failed=0)
        print(f"  ✓ {n_rows} movements loaded into core.movements")
        print(f"  ✓ inventory updated")
        print(f"  ✓ {len(cleaned_ids)} cleaned movements marked as loaded")
        print("Done.")
    except Exception as e:
        tracker.fail(str(e))
        print(f"  ✗ Load failed — {e}")
        raise


if __name__ == "__main__":
    main()
