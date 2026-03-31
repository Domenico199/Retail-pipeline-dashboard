import pandas as pd
import numpy as np
import argparse
import os
from datetime import datetime, timedelta
from src.db import get_db_engine

def random_time(start_hour, end_hour, date):
    start = datetime.combine(date, datetime.min.time()) + timedelta(hours=start_hour)
    end = datetime.combine(date, datetime.min.time()) + timedelta(hours=end_hour)
    return start + (end - start) * np.random.random()

def main(simulation_date):
    engine = get_db_engine()

    date = pd.to_datetime(simulation_date).date()

    specs = pd.read_sql("SELECT * FROM sim.products_specifications", engine)
    inventory = pd.read_sql("SELECT * FROM core.inventory", engine)
    suppliers = pd.read_sql("SELECT * FROM core.product_suppliers", engine)

    products_prices = pd.read_sql(
        "SELECT product_id, sale_price, purchase_price FROM core.products", engine
    ).set_index("product_id")

    PROMO_TYPES = ["sconto_percentuale", "offerta_3x2", "prezzo_speciale"]

    movements = []

    for _, row in specs.iterrows():
        product_id = row["product_id"]

        stock = inventory.loc[inventory["product_id"] == product_id, "stock_qty"].values
        stock = stock[0] if len(stock) else 0

        # --- SALES ---
        if row["assortment_flag"]:
            prob = {"high": 0.8, "medium": 0.5, "low": 0.2}[row["rotation_class"]]

            if np.random.rand() < prob:
                n_events = np.random.randint(1, 10)

                for _ in range(n_events):
                    qty = np.random.randint(1, 4)
                    is_promo = np.random.rand() < 0.15
                    movements.append({
                        "store_id": 1,
                        "product_id": product_id,
                        "supplier_id": None,
                        "movement_type": "sale",
                        "quantity": qty,
                        "unit_sale_price": float(products_prices.loc[product_id, "sale_price"]),
                        "unit_purchase_price": None,
                        "is_promo": is_promo,
                        "promo_type": np.random.choice(PROMO_TYPES) if is_promo else None,
                        "movement_timestamp": random_time(8, 20, date),
                        "movement_date": date
                    })

        # --- BREAKAGE ---
        if np.random.rand() < row["spoilage_probability"]:
            movements.append({
                "store_id": 1,
                "product_id": product_id,
                "supplier_id": None,
                "movement_type": "breakage",
                "quantity": np.random.randint(1, 3),
                "unit_sale_price": None,
                "unit_purchase_price": None,
                "is_promo": False,
                "promo_type": None,
                "movement_timestamp": random_time(6, 21, date),
                "movement_date": date
            })

        # --- PURCHASE ---
        if stock < row["minimum_stock_threshold"]:
            prod_sup = suppliers[suppliers["product_id"] == product_id]

            supplier_id = None
            qty = 0

            if len(prod_sup) > 0:
                chosen_supplier = prod_sup.sample(1).iloc[0]
                supplier_id = chosen_supplier["supplier_id"]

                if chosen_supplier["is_primary_supplier"]:
                    qty = int(row["reorder_lot"] * np.random.uniform(1.0, 1.5))
                else:
                    qty = int(row["reorder_lot"] * np.random.uniform(0.5, 1.0))

            if supplier_id:
                # se stock negativo, ordina almeno abbastanza per coprire il deficit
                if stock < 0:
                    qty = max(qty, abs(stock) + 1)
                movements.append({
                    "store_id": 1,
                    "product_id": product_id,
                    "supplier_id": supplier_id,
                    "movement_type": "purchase",
                    "quantity": max(1, qty),
                    "unit_sale_price": None,
                    "unit_purchase_price": float(products_prices.loc[product_id, "purchase_price"]),
                    "is_promo": False,
                    "promo_type": None,
                    "movement_timestamp": random_time(6, 17, date),
                    "movement_date": date
                })

    df = pd.DataFrame(movements)

    os.makedirs("data/source", exist_ok=True)
    file_path = f"data/source/movements_{date}.csv"
    df.to_csv(file_path, index=False)

    print(f"Generated {len(df)} movements → {file_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--date", required=True)
    args = parser.parse_args()

    main(args.date)