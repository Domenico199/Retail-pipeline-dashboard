import random
from typing import Tuple

import pandas as pd
from sqlalchemy import text

from src.db import get_db_engine


SEED = 42
random.seed(SEED)


# ----------------------------
# Regole base per cat1
# ----------------------------
CAT1_RULES = {
    "SCATOLAME DOLCE": {
        "rotation_class": "medium",
        "spoilage_range": (0.001, 0.004),
    },
    "SCATOLAME SALATO": {
        "rotation_class": "medium",
        "spoilage_range": (0.0005, 0.003),
    },
    "BEVANDE": {
        "rotation_class": "medium",
        "spoilage_range": (0.0001, 0.002),
    },
    "SURGELATI": {
        "rotation_class": "medium",
        "spoilage_range": (0.002, 0.008),
    },
    "MACELLERIA": {
        "rotation_class": "high",
        "spoilage_range": (0.03, 0.08),
    },
    "FRUTTA E VERDURA": {
        "rotation_class": "high",
        "spoilage_range": (0.04, 0.10),
    },
    "PANETTERIA": {
        "rotation_class": "high",
        "spoilage_range": (0.05, 0.12),
    },
    "CURA CASA": {
        "rotation_class": "medium",
        "spoilage_range": (0.0, 0.001),
    },
    "CURA PERSONA": {
        "rotation_class": "low",
        "spoilage_range": (0.0, 0.001),
    },
    "BAZAR LEGGERO": {
        "rotation_class": "low",
        "spoilage_range": (0.0, 0.0005),
    },
    "FRESCHI": {
        "rotation_class": "medium",
        "spoilage_range": (0.003, 0.02),
    },
    "GASTRONOMIA": {
        "rotation_class": "medium",
        "spoilage_range": (0.01, 0.04),
    },
}


# ----------------------------
# Override per cat2
# ----------------------------
CAT2_RULES = {
    "ACQUA": {
        "rotation_class": "high",
        "spoilage_range": (0.0001, 0.0005),
    },
    "BEVANDE GASSATE": {
        "rotation_class": "high",
        "spoilage_range": (0.0001, 0.001),
    },
    "BEVANDE PIATTE": {
        "rotation_class": "high",
        "spoilage_range": (0.0001, 0.001),
    },
    "PASTA": {
        "rotation_class": "high",
        "spoilage_range": (0.0005, 0.002),
    },
    "LATTE E PANNA FRESCA": {
        "rotation_class": "high",
        "spoilage_range": (0.02, 0.05),
    },
    "YOGURT": {
        "rotation_class": "medium",
        "spoilage_range": (0.02, 0.05),
    },
    "FORMAGGI": {
        "rotation_class": "medium",
        "spoilage_range": (0.015, 0.04),
    },
    "SALUMI": {
        "rotation_class": "medium",
        "spoilage_range": (0.015, 0.04),
    },
    "LATTICINI UHT ED ASSIMILABILI": {
        "rotation_class": "medium",
        "spoilage_range": (0.001, 0.004),
    },
    "LATTICINI UHT - PANNA E BESCIAMELLA": {
        "rotation_class": "medium",
        "spoilage_range": (0.001, 0.004),
    },
    "CHAMPAGNE E SPUMANTI": {
        "rotation_class": "low",
        "spoilage_range": (0.0001, 0.0005),
    },
    "VINO": {
        "rotation_class": "low",
        "spoilage_range": (0.0001, 0.0005),
    },
    "APERITIVI": {
        "rotation_class": "low",
        "spoilage_range": (0.0001, 0.0005),
    },
    "PANE E FOCACCE FROZEN": {
        "rotation_class": "medium",
        "spoilage_range": (0.01, 0.03),
    },
    "TERZA E QUARTA GAMMA": {
        "rotation_class": "high",
        "spoilage_range": (0.04, 0.10),
    },
    "MODULO REFRIGERATO": {
        "rotation_class": "medium",
        "spoilage_range": (0.02, 0.05),
    },
    "PARAFARMACEUTICO": {
        "rotation_class": "low",
        "spoilage_range": (0.0, 0.0005),
    },
    "PRIMA INFANZIA - PANNOLINI": {
        "rotation_class": "medium",
        "spoilage_range": (0.0, 0.0005),
    },
}


# ----------------------------
# Override per cat3
# ----------------------------
CAT3_RULES = {
    "ACQUA NON GASSATA": {
        "rotation_class": "high",
        "spoilage_range": (0.0001, 0.0005),
    },
    "ACQUA GASSATA": {
        "rotation_class": "high",
        "spoilage_range": (0.0001, 0.0005),
    },
    "ACQUA EFFERVESCENTE NATURALE": {
        "rotation_class": "high",
        "spoilage_range": (0.0001, 0.0005),
    },
    "LATTE UHT": {
        "rotation_class": "high",
        "spoilage_range": (0.001, 0.003),
    },
    "MOZZARELLE": {
        "rotation_class": "high",
        "spoilage_range": (0.03, 0.06),
    },
    "RICOTTA": {
        "rotation_class": "medium",
        "spoilage_range": (0.03, 0.06),
    },
    "YOGURT INTERO": {
        "rotation_class": "medium",
        "spoilage_range": (0.02, 0.05),
    },
    "PANE INDUSTRIALE E MEDIA E LUNGA CONSERVAZIONE": {
        "rotation_class": "medium",
        "spoilage_range": (0.01, 0.02),
    },
    "PANINI": {
        "rotation_class": "high",
        "spoilage_range": (0.05, 0.12),
    },
    "CIABATTE": {
        "rotation_class": "high",
        "spoilage_range": (0.05, 0.12),
    },
    "PIZZE FOCACCE": {
        "rotation_class": "high",
        "spoilage_range": (0.05, 0.12),
    },
    "MELE": {
        "rotation_class": "high",
        "spoilage_range": (0.03, 0.07),
    },
    "BANANE": {
        "rotation_class": "high",
        "spoilage_range": (0.05, 0.10),
    },
    "POMODORI": {
        "rotation_class": "high",
        "spoilage_range": (0.04, 0.08),
    },
    "ZUCCHINE/ZUCCHE": {
        "rotation_class": "high",
        "spoilage_range": (0.04, 0.08),
    },
    "LATTUGHE": {
        "rotation_class": "high",
        "spoilage_range": (0.06, 0.12),
    },
    "TONNO SOTT'OLIO": {
        "rotation_class": "high",
        "spoilage_range": (0.0005, 0.002),
    },
    "PASSATA DI POMODORO": {
        "rotation_class": "high",
        "spoilage_range": (0.0005, 0.002),
    },
    "PELATI E POMODORINI": {
        "rotation_class": "medium",
        "spoilage_range": (0.0005, 0.002),
    },
    "FAGIOLI CONSERVATI": {
        "rotation_class": "medium",
        "spoilage_range": (0.0005, 0.002),
    },
    "LAVASTOVIGLIE": {
        "rotation_class": "medium",
        "spoilage_range": (0.0, 0.0005),
    },
    "CANDEGGINA": {
        "rotation_class": "medium",
        "spoilage_range": (0.0, 0.0005),
    },
    "AMMORBIDENTI": {
        "rotation_class": "medium",
        "spoilage_range": (0.0, 0.0005),
    },
    "CHAMPAGNE E SPUMANTI": {
        "rotation_class": "low",
        "spoilage_range": (0.0001, 0.0005),
    },
}


# ----------------------------
# Parametri per classe di rotazione
# ----------------------------
ROTATION_STOCK_RULES = {
    "high": {
        "initial_stock": (40, 120),
        "minimum_stock_threshold": (12, 30),
        "reorder_lot": (30, 90),
    },
    "medium": {
        "initial_stock": (15, 50),
        "minimum_stock_threshold": (5, 12),
        "reorder_lot": (15, 40),
    },
    "low": {
        "initial_stock": (4, 20),
        "minimum_stock_threshold": (1, 5),
        "reorder_lot": (4, 15),
    },
}


def random_float(low: float, high: float, decimals: int = 5) -> float:
    return round(random.uniform(low, high), decimals)


def random_int(low: int, high: int) -> int:
    return random.randint(low, high)


def get_base_rule(cat1: str) -> dict:
    return CAT1_RULES.get(
        cat1,
        {
            "rotation_class": "medium",
            "spoilage_range": (0.005, 0.02),
        },
    )


def apply_overrides(cat1: str, cat2: str, cat3: str) -> Tuple[str, Tuple[float, float]]:
    rule = get_base_rule(cat1).copy()

    if cat2 in CAT2_RULES:
        rule.update(CAT2_RULES[cat2])

    if cat3 in CAT3_RULES:
        rule.update(CAT3_RULES[cat3])

    return rule["rotation_class"], rule["spoilage_range"]


def build_assortment_flag(cat1: str, cat2: str, cat3: str) -> bool:
    """
    Flag sintetico: il prodotto è potenzialmente in assortimento.
    Per ora lasciamo quasi tutti TRUE e rendiamo false solo poche categorie a rotazione bassa
    con una piccola probabilità.
    """
    low_rotation_categories = {"BAZAR LEGGERO", "CURA PERSONA"}
    if cat1 in low_rotation_categories:
        return random.random() > 0.15
    return random.random() > 0.03


def generate_product_specifications(df_products: pd.DataFrame) -> pd.DataFrame:
    rows = []

    for _, row in df_products.iterrows():
        product_id = row["product_id"]
        cat1 = row["category_level_1"]
        cat2 = row["category_level_2"]
        cat3 = row["category_level_3"]

        rotation_class, spoilage_range = apply_overrides(cat1, cat2, cat3)

        spoilage_probability = random_float(*spoilage_range)

        assortment_flag = build_assortment_flag(cat1, cat2, cat3)

        if assortment_flag:
            stock_rule = ROTATION_STOCK_RULES[rotation_class]
            initial_stock = random_int(*stock_rule["initial_stock"])
            minimum_stock_threshold = random_int(*stock_rule["minimum_stock_threshold"])
            reorder_lot = random_int(*stock_rule["reorder_lot"])

            if minimum_stock_threshold >= initial_stock:
                minimum_stock_threshold = max(1, initial_stock // 3)
        else:
            initial_stock = 0
            minimum_stock_threshold = 0
            reorder_lot = 0

        rows.append(
            {
                "product_id": product_id,
                "rotation_class": rotation_class,
                "spoilage_probability": spoilage_probability,
                "initial_stock": initial_stock,
                "minimum_stock_threshold": minimum_stock_threshold,
                "reorder_lot": reorder_lot,
                "assortment_flag": assortment_flag,
            }
        )

    return pd.DataFrame(rows)


def main():
    engine = get_db_engine()

    # controllo se la tabella contiene già dati
    with engine.connect() as conn:
        result = conn.execute(text("SELECT COUNT(*) FROM sim.products_specifications"))
        row_count = result.scalar()

    if row_count > 0:
        print(f"sim.products_specifications already contains {row_count} rows. Load skipped.")
        return

    query = """
        SELECT
            product_id,
            category_level_1,
            category_level_2,
            category_level_3
        FROM core.products
    """

    df_products = pd.read_sql(query, engine)

    print(f"Loaded {len(df_products)} products from core.products")

    df_specs = generate_product_specifications(df_products)

    print("Generated product specifications:")
    print(df_specs.head())

    df_specs.to_sql(
        name="products_specifications",
        con=engine,
        schema="sim",
        if_exists="append",
        index=False,
        chunksize=500,
    )

    print("sim.products_specifications successfully populated.")


if __name__ == "__main__":
    main()