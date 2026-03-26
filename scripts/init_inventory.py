import pandas as pd
import numpy as np
from src.db import get_db_engine

def main():
    engine = get_db_engine()

    specs = pd.read_sql("""
        SELECT product_id, initial_stock, assortment_flag
        FROM sim.products_specifications
    """, engine)

    rows = []

    for _, row in specs.iterrows():
        stock = row["initial_stock"] if row["assortment_flag"] else 0

        rows.append({
            "store_id": 1,
            "product_id": row["product_id"],
            "stock_qty": stock
        })

    df = pd.DataFrame(rows)

    df.to_sql(
        "inventory",
        engine,
        schema="core",
        if_exists="replace",
        index=False
    )

    print("Inventory initialized")

if __name__ == "__main__":
    main()