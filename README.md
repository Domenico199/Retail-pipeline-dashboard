# Retail Store Data Pipeline & Analytics

Progetto portfolio end-to-end: simulazione dati operativi di un punto vendita, pipeline ETL, layer analytics e orchestrazione. Dimostra competenze di data engineering su uno stack moderno.

---

## Architettura

Il progetto segue un'architettura a 3 layer con schema PostgreSQL dedicati:

```
CSV (simulated API)
        |
        v
  +-----------+       +-----------+       +-------------+
  |  staging  |  -->  |   core    |  -->  |  analytics  |
  |  (raw)    |       | (cleaned) |       |  (views)    |
  +-----------+       +-----------+       +-------------+
                                                |
                                                v
                                          Dashboard BI
```

- **`staging`** — dati grezzi dal CSV, nessun vincolo FK/CHECK (validazione delegata al transform)
- **`core`** — dati puliti, normalizzati, con vincoli di integrità
- **`analytics`** — view SQL aggregate, pronte per il consumo BI
- **`sim`** — parametri per la generazione dati sintetici (rotation class, spoilage probability, ecc.)

---

## Pipeline ETL

La pipeline è suddivisa in 3 step sequenziali, ciascuno idempotente:

### 1. Extract (`pipeline/extract/extract_raw_movements.py`)
- Legge file CSV da `data/source/`
- Carica in `staging.raw_movements` senza trasformazioni
- Traccia i file processati in `staging.processed_files` (no duplicati)

### 2. Transform (`pipeline/transform/transform_raw_movements.py`)
- Legge da `staging.raw_movements`
- Applica 6 regole di validazione (prodotto sconosciuto, fornitore mancante, prezzi incoerenti, ecc.)
- Output: `staging.cleaned_movements` (validi) + `staging.bad_movements` (scarti con motivo)

### 3. Load (`pipeline/load/load_movements.py`)
- Legge `staging.cleaned_movements` dove `loaded = FALSE`
- Arricchisce con posizione scaffale da `core.store_assortment` (denormalizzazione storica)
- Inserisce in `core.movements` e aggiorna `core.inventory`
- Tutto in singola transazione (atomicita')
- Marca i record come `loaded = TRUE`

### Observability
Ogni step registra esecuzione, durata, righe processate/fallite in `staging.pipeline_runs` tramite il helper `RunTracker`.

---

## Analytics Layer

8 view SQL in `analytics`, progettate per il consumo diretto da tool BI:

| View | Descrizione |
|------|-------------|
| `sales_by_shelf_historical` | Vendite per scaffale (posizione al momento della vendita) |
| `sales_by_shelf_current` | Vendite per scaffale (posizione attuale del prodotto) |
| `breakage_by_shelf_historical` | Rotture per scaffale (storico) |
| `breakage_by_shelf_current` | Rotture per scaffale (corrente) |
| `margins_by_product_shelf` | Margini per prodotto/scaffale (revenue vs costo) |
| `daily_kpis` | KPI giornalieri aggregati (vendite, rotture, acquisti) |
| `inventory_by_shelf` | Stock attuale per posizione con fill percentage |
| `shelf_detail` | Dimensione scaffale per BI (layout + prodotto assegnato) |

Le view **historical** usano `movements.shelf_id` (dove era il prodotto quando è stato venduto).
Le view **current** usano `store_assortment.shelf_id` (dove è il prodotto adesso).

---

## Orchestrazione

**Apache Airflow** orchestra la pipeline con un DAG giornaliero:

```
extract >> transform >> load
```

- DAG: `retail_pipeline` (`dags/retail_pipeline_dag.py`)
- Schedule: `@daily`
- Docker Compose con webserver, scheduler e metadata DB dedicato

---

## Schema Migrations

**Alembic** gestisce l'evoluzione dello schema:

| Migration | Descrizione |
|-----------|-------------|
| `201a206eb191` | Baseline |
| `ad2b2eb4f887` | Rimozione FK/CHECK da raw_movements |
| `3bf22fb601f1` | Trigger updated_at su inventory |
| `07c7eb570292` | Tabella pipeline_runs |
| `ec8a1f10e303` | Colonna updated_at su inventory |
| `a1b2c3d4e5f6` | View analytics (8 view) |

---

## Stack Tecnologico

| Componente | Tecnologia |
|------------|------------|
| Linguaggio | Python 3.12 |
| Database | PostgreSQL 16 |
| ORM / DB access | SQLAlchemy + psycopg2 |
| Data manipulation | Pandas |
| Migrations | Alembic |
| Orchestrazione | Apache Airflow |
| Containerizzazione | Docker + Docker Compose |
| Package management | pyproject.toml (editable install) |

---

## Struttura del Progetto

```
Retail/
├── alembic/                        # Schema migrations
│   ├── env.py
│   └── versions/                   # 6 migration files
│
├── dags/
│   └── retail_pipeline_dag.py      # Airflow DAG
│
├── data/
│   ├── master/                     # CSV anagrafiche (products, suppliers, layout, ecc.)
│   └── source/                     # CSV movimenti giornalieri (output simulatore)
│
├── pipeline/
│   ├── extract/
│   │   └── extract_raw_movements.py
│   ├── transform/
│   │   └── transform_raw_movements.py
│   ├── load/
│   │   └── load_movements.py
│   └── run_tracker.py              # Helper observability
│
├── scripts/
│   ├── simulate_api_daily_dump.py  # Generatore movimenti giornalieri
│   ├── backfill.py                 # Backfill day-by-day (simulate + pipeline)
│   ├── load_products_master.py     # Caricamento anagrafica prodotti
│   ├── load_suppliers.py           # Caricamento fornitori
│   ├── load_product_suppliers.py   # Relazioni prodotto-fornitore
│   ├── generate_store_layout.py    # Generazione layout scaffali
│   ├── generate_store_assortment.py# Generazione assortimento
│   ├── generate_products_specifications.py  # Parametri simulazione
│   └── init_inventory.py           # Inizializzazione stock
│
├── sql/
│   ├── 01_create_schemas.sql
│   ├── 02_create_tables_core.sql
│   ├── 03_create_tables_sim.sql
│   ├── 04_create_tables_staging.sql
│   ├── 05_create_tables_core_movements.sql
│   ├── 06_create_tables_staging_validation.sql
│   ├── 07_create_tables_staging_pipeline_runs.sql
│   └── 08_create_views_analytics.sql
│
├── src/
│   └── db.py                       # Engine factory (get_db_engine)
│
├── notebook/
│   └── mod_data.ipynb              # Esplorazione dati
│
├── Dockerfile.airflow
├── docker-compose.yaml
├── pyproject.toml
├── requirements.txt
├── alembic.ini
└── .env                            # Credenziali DB (non versionato)
```

---

## Come Eseguire il Progetto

### 1. Setup ambiente

```bash
# Avvia PostgreSQL
docker compose up -d postgres

# Installa dipendenze
pip install -e .

# Crea schema e tabelle
psql -f sql/01_create_schemas.sql
psql -f sql/02_create_tables_core.sql
psql -f sql/03_create_tables_sim.sql
psql -f sql/04_create_tables_staging.sql
psql -f sql/05_create_tables_core_movements.sql
psql -f sql/06_create_tables_staging_validation.sql
psql -f sql/07_create_tables_staging_pipeline_runs.sql
```

### 2. Caricamento master data

```bash
python -m scripts.load_products_master
python -m scripts.load_suppliers
python -m scripts.load_product_suppliers
python -m scripts.generate_store_layout
python -m scripts.generate_store_assortment
python -m scripts.generate_products_specifications
python -m scripts.init_inventory
```

### 3. Applicazione migrations

```bash
alembic upgrade head
```

### 4. Backfill dati storici

```bash
python -m scripts.backfill --start 2026-01-01 --end 2026-03-31
```

### 5. Avvio Airflow (orchestrazione)

```bash
docker compose up -d
```

---

## Scelte di Modellazione

### Prezzi statici
Nel modello reale, costo e prezzo variano nel tempo (SCD Type 2). In questo progetto sono statici in `core.products`. Il prezzo effettivo delle vendite (incluse promo) e' comunque tracciato in `core.movements.unit_sale_price`.

### Denormalizzazione posizione scaffale
`core.movements` include `shelf_id`, `shelf_level`, `zone`, `slot_number` copiati da `store_assortment` al momento del load. Questo permette analisi storiche accurate anche se un prodotto viene spostato.

### Raw layer senza vincoli
`staging.raw_movements` non ha FK ne' CHECK constraint. I dati arrivano "as-is" e la validazione avviene nel transform step, separando nettamente ingestion da data quality.

### Tabella `sim.products_specifications`
Contiene parametri per la generazione dati (rotation class, spoilage probability, stock iniziale, ecc.). Non rappresenta dati reali ma solo logica simulativa.

---

## Limitazioni e Possibili Evoluzioni

### Limitazioni attuali
- Prezzi non storicizzati (no SCD)
- Single-store (predisposto multi-store con `store_id`)
- No real-time streaming
- Inventory senza gestione lotti

### Possibili evoluzioni
- Storico prezzi (SCD Type 2)
- Multi-store
- Streaming con Kafka
- Deploy cloud (AWS/Azure)
- Data quality checks avanzati (Great Expectations)
- Dashboard BI (Apache Superset)

---

## Stato del Progetto

- [x] Data model (staging / core / sim)
- [x] Simulatore dati giornalieri
- [x] Pipeline ETL (extract / transform / load)
- [x] Pipeline observability (RunTracker + pipeline_runs)
- [x] Schema migrations (Alembic)
- [x] Backfill storico (~90 giorni)
- [x] Orchestrazione (Airflow + Docker Compose)
- [x] Analytics layer (8 view SQL)
- [ ] Dashboard BI

---

## Autore

**Domenico Serino**

Progetto realizzato a scopo portfolio Data Engineering.
