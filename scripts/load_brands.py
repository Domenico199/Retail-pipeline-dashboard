"""
Genera il CSV dei brand e lo carica in core.brands.
Assegna nomi famosi di brand italiani/internazionali ai brand_code esistenti.
"""

import pandas as pd
from sqlalchemy import text
from src.db import get_db_engine

# Lista di brand famosi nei supermercati italiani
FAMOUS_BRANDS = [
    # Alimentari
    "Barilla", "De Cecco", "Voiello", "Delverde", "Rummo",
    "Nestlé", "Ferrero", "Kinder", "Nutella", "Tic Tac",
    "Mulino Bianco", "Pavesi", "Bistefan", "Galbusera", "Balocco",
    "Lavazza", "Illy", "Kimbo", "Segafredo", "Nescafé",
    "Galbani", "Parmalat", "Granarolo", "Yomo", "Danone",
    "Findus", "Bonduelle", "Valfrutta", "Cirio", "Mutti",
    "Buitoni", "Panzani", "Star", "Knorr", "Maggi",
    "Rio Mare", "Calvo", "Simmenthal", "Nostromo", "Bolton",
    "Heinz", "Kraft", "Hellmann's", "Philadelphia", "Kellogg's",
    "Riso Scotti", "Riso Gallo", "Curtiriso", "Scotti", "Vivo",
    "Coca-Cola", "Pepsi", "Sprite", "Fanta", "Red Bull",
    "San Pellegrino", "Ferrarelle", "Levissima", "Acqua Panna", "Uliveto",
    "Lipton", "Twinings", "Pompadour", "Yogi Tea", "Tetley",
    # Cura persona
    "L'Oréal", "Garnier", "Pantene", "Head & Shoulders", "Dove",
    "Nivea", "Neutrogena", "Maybelline", "Colgate", "Oral-B",
    "Gillette", "AXE", "Rexona", "Sebamed", "Bioderma",
    "Borotalco", "Roberts", "Lysoform", "Vidal", "Johnson",
    # Casa & pulizia
    "Ariel", "Dash", "Lenor", "Fairy", "Flash",
    "Cif", "Domestos", "Ace", "Bref", "Candeggina Regina",
    "Scottex", "Regina", "Tempo", "Fazzolettini Soft", "Kleenex",
    "Perlana", "Svelto", "Coccolino", "Omino Bianco", "Bioil",
    # Freschi & gastronomia
    "Beretta", "Rovagnati", "Fiorucci", "Negroni", "Levoni",
    "Rigamonti", "Citterio", "Salumificio Italia", "Calabrese", "Pini",
    "Casa Modena", "Mortadella Bologna", "Prosciutto San Daniele", "Culatello Podere", "Bresaola Rigamonti",
    "Milka", "Toblerone", "Lindt", "Baci Perugina", "Venchi",
    "Pringles", "Lay's", "Snack d'Or", "Amica Chips", "San Carlo",
    # Vini & alcolici
    "Martini", "Campari", "Aperol", "Ramazzotti", "Montenegro",
    "Birra Moretti", "Peroni", "Heineken", "Corona", "Beck's",
    "Contadino", "Tavernello", "Bolla", "Riunite", "Zonin",
]

def main():
    engine = get_db_engine()

    # Recupera tutti i brand_code esistenti in products
    with engine.connect() as conn:
        result = conn.execute(text(
            "SELECT DISTINCT brand_code FROM core.products WHERE brand_code IS NOT NULL ORDER BY brand_code"
        ))
        brand_codes = [row[0] for row in result]

    print(f"Brand codes trovati: {len(brand_codes)}")

    # Assegna un nome famoso a ogni brand_code
    rows = []
    for i, code in enumerate(brand_codes):
        brand_name = FAMOUS_BRANDS[i % len(FAMOUS_BRANDS)]
        # Se il nome è già usato, aggiungi un suffisso
        used_names = [r["brand_name"] for r in rows]
        if brand_name in used_names:
            brand_name = f"{brand_name} {i // len(FAMOUS_BRANDS) + 2}"
        rows.append({"brand_code": code, "brand_name": brand_name})

    df = pd.DataFrame(rows)

    # Salva CSV
    csv_path = "data/brands.csv"
    df.to_csv(csv_path, index=False)
    print(f"CSV salvato: {csv_path}")

    # Crea tabella se non esiste e carica i dati
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS core.brands (
                brand_code  VARCHAR(20) PRIMARY KEY,
                brand_name  VARCHAR(100) NOT NULL,
                created_at  TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """))

        # Upsert
        for _, row in df.iterrows():
            conn.execute(text("""
                INSERT INTO core.brands (brand_code, brand_name)
                VALUES (:code, :name)
                ON CONFLICT (brand_code) DO UPDATE SET brand_name = EXCLUDED.brand_name
            """), {"code": row["brand_code"], "name": row["brand_name"]})

    print(f"Caricati {len(df)} brand in core.brands")

    # Verifica
    result_df = pd.read_sql("SELECT * FROM core.brands ORDER BY brand_code LIMIT 10", engine)
    print("\nSample:")
    print(result_df.to_string(index=False))


if __name__ == "__main__":
    main()
