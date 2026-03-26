import pandas as pd
from sqlalchemy import text
from src.db import get_db_engine

def main():
    engine = get_db_engine()

    suppliers = []

    # 1 fornitore principale
    suppliers.append({
        "supplier_id": "SUP_001",
        "supplier_name": "Fornitore A",
        "supplier_type": "primary"
    })

    # 19 secondari
    for i in range(2, 21):
        suppliers.append({
            "supplier_id": f"SUP_{i:03}",
            "supplier_name": f"Fornitore {chr(64+i)}",
            "supplier_type": "secondary"
        })

    df = pd.DataFrame(suppliers)

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE core.suppliers CASCADE"))
    df.to_sql(
        "suppliers",
        engine,
        schema="core",
        if_exists="append",
        index=False
    )

    print("Suppliers loaded")

if __name__ == "__main__":
    main()