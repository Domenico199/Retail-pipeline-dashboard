import pandas as pd
from sqlalchemy import text

from src.db import get_db_engine

STORE_ID = 1
N_SHELVES = 45
LEVELS = [1, 2, 3, 4, 5]
ZONES = ["left", "center", "right"]
SLOTS = [1, 2, 3]


def generate_layout():
    rows = []

    for shelf_id in range(1, N_SHELVES + 1):
        for level in LEVELS:
            for zone in ZONES:
                for slot in SLOTS:
                    rows.append({
                        "store_id": STORE_ID,
                        "shelf_id": shelf_id,
                        "shelf_category": None,
                        "shelf_level": level,
                        "zone": zone,
                        "slot_number": slot
                    })

    df = pd.DataFrame(rows)
    return df


def main():
    engine = get_db_engine()

    df_layout = generate_layout()

    print(f"Generated {len(df_layout)} shelf slots")

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE core.store_layout CASCADE"))

    df_layout.to_sql(
        name="store_layout",
        con=engine,
        schema="core",
        if_exists="append",
        index=False
    )

    print("Store layout loaded successfully.")


if __name__ == "__main__":
    main()