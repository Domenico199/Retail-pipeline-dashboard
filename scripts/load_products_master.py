import pandas as pd
from pathlib import Path
from sqlalchemy import text

from src.db import get_db_engine

"""
Script used to load the products master data (product registry)
into the core.products table.

The source CSV should contain the anonymized product registry
created during the data preparation phase.
"""

DATA_PATH = Path("data/products_master.csv")

COLUMN_MAPPING = {
    "id_prodotto": "product_id",
    "descrizione": "product_description",
    "cat1": "category_level_1",
    "cat2": "category_level_2",
    "cat3": "category_level_3",
    "iva": "vat_rate",
    "um": "unit_of_measure",
    "costo": "purchase_price",
    "prezzo_vendita": "sale_price",
    "brand": "brand_code",
}


def main():

    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Products master file not found at: {DATA_PATH}"
        )

    engine = get_db_engine()

    # controllo se la tabella contiene già dati
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM core.products"))
        row_count = result.scalar()

    if row_count > 0:
        print(f"core.products already contains {row_count} rows. Load skipped.")
        return

    print("Reading products master file...")

    df = pd.read_csv(DATA_PATH)

    # rinomina le colonne secondo lo schema del DB
    df = df.rename(columns=COLUMN_MAPPING)

    # mantiene solo le colonne necessarie
    df = df[list(COLUMN_MAPPING.values())]

    print("Loading products into core.products...")

    df.to_sql(
        name="products",
        con=engine,
        schema="core",
        if_exists="append",
        index=False,
        chunksize=100,
    )

    print("Products successfully loaded.")


if __name__ == "__main__":
    main()