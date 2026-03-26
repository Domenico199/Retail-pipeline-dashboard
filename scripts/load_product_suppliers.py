import pandas as pd
import numpy as np
from src.db import get_db_engine

def main():
    engine = get_db_engine()

    products = pd.read_sql("SELECT product_id FROM core.products", engine)
    suppliers = pd.read_sql("SELECT * FROM core.suppliers", engine)

    primary_supplier = suppliers[suppliers["supplier_type"] == "primary"].iloc[0]
    secondary_suppliers = suppliers[suppliers["supplier_type"] == "secondary"]

    rows = []

    for _, row in products.iterrows():
        product_id = row["product_id"]

        rand = np.random.rand()

        # --- 70% SOLO PRIMARY ---
        if rand < 0.70:
            rows.append({
                "product_id": product_id,
                "supplier_id": primary_supplier["supplier_id"],
                "is_primary_supplier": True
            })

        # --- 25% SOLO SECONDARIO ---
        elif rand < 0.95:
            s = secondary_suppliers.sample(1).iloc[0]

            rows.append({
                "product_id": product_id,
                "supplier_id": s["supplier_id"],
                "is_primary_supplier": False
            })

        # --- 5% PRIMARY + SECONDARIO ---
        else:
            # primary
            rows.append({
                "product_id": product_id,
                "supplier_id": primary_supplier["supplier_id"],
                "is_primary_supplier": True
            })

            # secondary
            s = secondary_suppliers.sample(1).iloc[0]

            rows.append({
                "product_id": product_id,
                "supplier_id": s["supplier_id"],
                "is_primary_supplier": False
            })

    df = pd.DataFrame(rows)

    df.to_sql(
        "product_suppliers",
        engine,
        schema="core",
        if_exists="replace",
        index=False
    )

    print("Product suppliers loaded")

if __name__ == "__main__":
    main()