import random
import pandas as pd
from sqlalchemy import text

from src.db import get_db_engine

TOTAL_SHELVES = 45
STORE_ID = 1
TARGET_PRODUCTS_IN_ASSORTMENT = 2000
PRODUCTS_PER_SHELF = 45
SEED = 42

random.seed(SEED)


def load_data(engine):
    products = pd.read_sql("SELECT * FROM core.products", engine)
    specs = pd.read_sql("SELECT * FROM sim.products_specifications", engine)
    layout = pd.read_sql(
        f"SELECT * FROM core.store_layout WHERE store_id = {STORE_ID}",
        engine,
    )

    df = products.merge(specs, on="product_id")

    # Solo prodotti candidati all'assortimento
    df = df[df["assortment_flag"] == True].copy()

    return df, layout


def compute_shelves_per_category(df):
    counts = df.groupby("category_level_1").size().sort_values(ascending=False)
    weights = counts / counts.sum()

    shelves = (weights * TOTAL_SHELVES).round().astype(int)

    diff = TOTAL_SHELVES - shelves.sum()
    if diff != 0:
        # aggiusta partendo dalla categoria con più prodotti
        first_category = shelves.index[0]
        shelves.loc[first_category] += diff

    return shelves.to_dict()


def build_shelf_category_map(shelves_map):
    shelf_category_map = {}
    shelf_id = 1

    for category, n_shelves in shelves_map.items():
        for _ in range(n_shelves):
            shelf_category_map[shelf_id] = category
            shelf_id += 1

    return shelf_category_map


def pick_unique_products_for_shelf(available_df, shelf_category, n_products=45):
    """
    Seleziona prodotti unici per scaffale:
    - ~70% categoria principale
    - ~30% altre categorie
    - mix di rotation_class se possibile
    """
    main_df = available_df[available_df["category_level_1"] == shelf_category].copy()
    other_df = available_df[available_df["category_level_1"] != shelf_category].copy()

    n_main_target = int(n_products * 0.7)
    n_other_target = n_products - n_main_target

    main_selected = main_df.sample(min(n_main_target, len(main_df)), replace=False) if len(main_df) > 0 else main_df.head(0)

    remaining_needed = n_products - len(main_selected)
    other_selected = other_df.sample(min(max(n_other_target, remaining_needed), len(other_df)), replace=False) if len(other_df) > 0 else other_df.head(0)

    selected = pd.concat([main_selected, other_selected]).drop_duplicates(subset=["product_id"])

    # se non bastano ancora, completa con altri prodotti disponibili
    if len(selected) < n_products:
        used_ids = set(selected["product_id"].tolist())
        remaining_pool = available_df[~available_df["product_id"].isin(used_ids)]
        if len(remaining_pool) > 0:
            top_up = remaining_pool.sample(min(n_products - len(selected), len(remaining_pool)), replace=False)
            selected = pd.concat([selected, top_up]).drop_duplicates(subset=["product_id"])

    # prova a mescolare un po' le classi di rotazione se ci sono abbastanza prodotti
    if len(selected) > 0:
        high = selected[selected["rotation_class"] == "high"]
        medium = selected[selected["rotation_class"] == "medium"]
        low = selected[selected["rotation_class"] == "low"]

        target_high = int(len(selected) * 0.3)
        target_medium = int(len(selected) * 0.5)
        target_low = len(selected) - target_high - target_medium

        balanced_parts = []

        if len(high) > 0:
            balanced_parts.append(high.sample(min(target_high, len(high)), replace=False))
        if len(medium) > 0:
            balanced_parts.append(medium.sample(min(target_medium, len(medium)), replace=False))
        if len(low) > 0:
            balanced_parts.append(low.sample(min(target_low, len(low)), replace=False))

        balanced = pd.concat(balanced_parts).drop_duplicates(subset=["product_id"]) if balanced_parts else selected.head(0)

        if len(balanced) < len(selected):
            used_ids = set(balanced["product_id"].tolist())
            missing = selected[~selected["product_id"].isin(used_ids)]
            balanced = pd.concat([balanced, missing]).drop_duplicates(subset=["product_id"])

        selected = balanced.sample(frac=1, random_state=SEED).reset_index(drop=True)

    return selected.head(n_products)


def generate_assortment(df, layout, shelves_map):
    # IMPORTANTE:
    # con il vincolo PK(store_id, product_id), ogni prodotto può comparire una sola volta.
    total_slots = len(layout)
    target_assignments = min(TARGET_PRODUCTS_IN_ASSORTMENT, len(df), total_slots)

    if TARGET_PRODUCTS_IN_ASSORTMENT < total_slots:
        print(
            f"WARNING: {total_slots} slot disponibili ma solo {TARGET_PRODUCTS_IN_ASSORTMENT} prodotti target. "
            f"Gli slot rimanenti resteranno vuoti nella v1."
        )

    shelf_category_map = build_shelf_category_map(shelves_map)
    shelf_slots = layout.sort_values(["shelf_id", "shelf_level", "zone", "slot_number"]).groupby("shelf_id")

    available_df = df.sample(frac=1, random_state=SEED).copy()
    rows = []

    for shelf_id, shelf_layout in shelf_slots:
        if len(rows) >= target_assignments:
            break

        shelf_category = shelf_category_map.get(shelf_id)
        if shelf_category is None:
            continue

        remaining_capacity = target_assignments - len(rows)
        n_for_shelf = min(PRODUCTS_PER_SHELF, remaining_capacity)

        chosen_products = pick_unique_products_for_shelf(
            available_df=available_df,
            shelf_category=shelf_category,
            n_products=n_for_shelf,
        )

        if chosen_products.empty:
            continue

        shelf_layout = shelf_layout.head(len(chosen_products)).reset_index(drop=True)
        chosen_products = chosen_products.reset_index(drop=True)

        for i in range(len(chosen_products)):
            rows.append({
                "store_id": STORE_ID,
                "product_id": chosen_products.loc[i, "product_id"],
                "shelf_id": int(shelf_layout.loc[i, "shelf_id"]),
                "shelf_level": int(shelf_layout.loc[i, "shelf_level"]),
                "zone": shelf_layout.loc[i, "zone"],
                "slot_number": int(shelf_layout.loc[i, "slot_number"]),
            })

        # rimuovi globalmente i prodotti già assegnati
        used_ids = set(chosen_products["product_id"].tolist())
        available_df = available_df[~available_df["product_id"].isin(used_ids)].copy()

    return pd.DataFrame(rows)


def main():
    engine = get_db_engine()

    print("Loading data...")
    df, layout = load_data(engine)

    print("Computing shelves distribution...")
    shelves_map = compute_shelves_per_category(df)

    print("Generating assortment...")
    df_assortment = generate_assortment(df, layout, shelves_map)

    print(f"Generated {len(df_assortment)} assignments")
    print(f"Unique assigned products: {df_assortment['product_id'].nunique()}")

    with engine.begin() as conn:
        conn.execute(text("TRUNCATE TABLE core.store_assortment"))

    df_assortment.to_sql(
        name="store_assortment",
        con=engine,
        schema="core",
        if_exists="append",
        index=False,
        chunksize=500,
    )

    print("Store assortment loaded successfully.")


if __name__ == "__main__":
    main()