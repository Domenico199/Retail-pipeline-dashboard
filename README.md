# Retail Store Analytics Platform

Progetto portfolio end-to-end per simulare l'integrazione dei dati di un punto vendita retail, costruire una pipeline dati e alimentare una dashboard analytics.

## Obiettivo

Simulare un sistema reale in cui un punto vendita invia ogni giorno i movimenti operativi (vendite, acquisti, avarie) e il mio prodotto:

- riceve i dati dal gestionale
- li standardizza
- li carica in un database strutturato
- costruisce un layer analytics
- alimenta una dashboard Power BI

Il progetto include anche la generazione di dati sintetici realistici per simulare:
- assortimento
- struttura scaffali
- stock
- movimenti giornalieri

## Architettura logica

1. **Master data**
   - anagrafica prodotti
   - assortimento
   - layout punto vendita
   - parametri di stock

2. **Daily feed simulato**
   - movimenti giornalieri:
     - vendite
     - acquisti
     - avarie

3. **Database**
   - `staging`: dati ricevuti quasi raw
   - `core`: dati puliti e standardizzati
   - `analytics`: modello per dashboard

4. **Dashboard**
   - KPI di vendita
   - margine
   - stock
   - avarie
   - analisi per categoria, brand e prodotto

## Scelte di modellazione

### Prezzi e costi nella tabella `core.products`
Nel modello reale, costo di acquisto e prezzo di vendita possono variare nel tempo e andrebbero storicizzati in tabelle dedicate, ad esempio:

- `product_cost_history`
- `product_price_history`

Per semplificare questo progetto, si assume che:

- `costo`
- `prezzo_vendita`

siano stabili nel periodo simulato e quindi vengano memorizzati come attributi della tabella `core.products`.

Questa è una semplificazione consapevole del modello, utile per mantenere il progetto gestibile nella fase iniziale pur mostrando consapevolezza di come andrebbe modellato in un contesto produttivo.

### Tabella `core.products_specifications` per la generazione dei dati fittizi
Per generare dati sintetici realistici è necessaria una tabella di supporto che contenga parametri non forniti normalmente da un punto vendita reale, ad esempio:

- classe di rotazione
- probabilità di avaria
- stock iniziale
- scorta minima
- lotto di riordino

Questi dati non rappresentano input reali del cliente, ma servono esclusivamente a simulare il comportamento operativo del negozio e produrre feed giornalieri coerenti.

Per questo motivo è stata introdotta la tabella:

- `core.products_specifications`

Questa tabella è presente solo per la generazione dei dati fittizi e non rappresenta una componente che, in uno scenario produttivo reale, verrebbe necessariamente fornita dal punto vendita.

## Stack tecnologico

- **Python**
- **PostgreSQL**
- **Docker**
- **SQLAlchemy**
- **Pandas**
- **Power BI**
- **Jupyter** (solo per esplorazione e prototipazione)

## Struttura del progetto

```text
RETAIL/
├── README.md
├── .gitignore
├── .env.example
├── docker-compose.yml
├── requirements.txt
│
├── docs/
│   ├── architecture.md
│   ├── data_model.md
│   ├── pipeline.md
│   └── dashboard.md
│
├── sql/
│   ├── 01_create_schemas.sql
│   ├── 02_create_tables_staging.sql
│   ├── 03_create_tables_core.sql
│   ├── 04_create_tables_analytics.sql
│   └── 05_views.sql
│
├── src/
│   ├── common/
│   │   ├── db.py
│   │   ├── paths.py
│   │   └── utils.py
│   │
│   ├── simulation/
│   │   ├── build_store_layout.py
│   │   ├── build_assortment.py
│   │   ├── build_inventory_parameters.py
│   │   ├── generate_daily_movements.py
│   │   └── export_daily_feed.py
│   │
│   ├── ingestion/
│   │   ├── load_daily_feed_to_staging.py
│   │   └── validate_feed.py
│   │
│   ├── transform/
│   │   ├── staging_to_core.py
│   │   └── core_to_analytics.py
│   │
│   └── analytics/
│       ├── build_dimensions.py
│       ├── build_facts.py
│       └── build_kpis.py
│
├── scripts/
│   ├── bootstrap_db.py
│   ├── load_products_master.py
│   ├── run_simulation.py
│   └── run_pipeline.py
│
├── data/
│   ├── sample/
│   │   ├── sample_products.csv
│   │   └── sample_daily_feed.csv
│   │
│   └── generated/
│       ├── store_layout.csv
│       ├── assortment.csv
│       ├── inventory_parameters.csv
│       └── daily_feed/
│
├── notebooks/
│   ├── 01_exploration.ipynb
│   └── 02_kpi_checks.ipynb
│
├── tests/
│   ├── test_simulation.py
│   ├── test_ingestion.py
│   └── test_transformations.py
│
└── dashboard/
    ├── powerbi/
    └── screenshots/
# Retail Store Analytics Platform

Progetto portfolio end-to-end per simulare un sistema dati retail, costruire una pipeline dati e alimentare una dashboard analytics.

---

## 🎯 Obiettivo

Simulare un contesto reale in cui un punto vendita invia quotidianamente i movimenti operativi (vendite, acquisti, avarie) e costruire un sistema dati che:

- acquisisce i dati da una sorgente esterna (simulata)
- li valida e standardizza
- li carica in un database strutturato
- costruisce un layer analytics
- alimenta una dashboard Power BI

Il progetto include anche la generazione di dati sintetici realistici per simulare:

- assortimento
- struttura scaffali
- stock
- comportamenti di vendita e riordino

---

## 🧱 Architettura logica

### 1. Master Data
- anagrafica prodotti
- fornitori
- assortimento
- layout punto vendita
- parametri di stock

### 2. Simulazione dati
- generazione giornaliera di movimenti:
  - vendite
  - acquisti
  - avarie
- output: file CSV (simulazione API)

### 3. Data Pipeline

- **Extract / Ingestion**
  - lettura file CSV da `data/source`
  - caricamento in `staging.raw_movements`

- **Transform (staging → core)**
  - validazione dati
  - standardizzazione
  - arricchimento
  - aggiornamento inventory

- **Transform (core → analytics)**
  - costruzione tabelle di reporting
  - aggregazioni KPI

### 4. Data Layers

- `staging` → dati raw
- `core` → dati puliti e normalizzati
- `analytics` → modello per BI

### 5. Dashboard

- KPI vendite
- margini
- stock
- avarie
- analisi per categoria, brand e prodotto

---

## ⚙️ Pipeline – funzionamento

La pipeline è progettata per essere eseguita giornalmente:

1. Scansione cartella `data/source`
2. Identificazione file non ancora processati
3. Caricamento in `staging.raw_movements`
4. Trasformazione e caricamento in `core.movements`
5. Aggiornamento `core.inventory`
6. Registrazione file in `staging.processed_files`

### Gestione failure

- i file non processati restano disponibili per retry
- la pipeline supporta il recupero automatico (catch-up)

---

## 🧠 Scelte di modellazione

### Prezzi e costi

Nel modello reale:
- i prezzi variano nel tempo
- servono tabelle storiche

In questo progetto:
- `purchase_price` e `sale_price` sono statici in `core.products`

👉 Semplificazione consapevole

---

### Simulazione dati (`sim.products_specifications`)

Contiene parametri per generare i dati:

- rotation_class
- spoilage_probability
- initial_stock
- minimum_stock_threshold
- reorder_lot

👉 Non rappresenta dati reali, ma solo logica simulativa

---

### Assortimento e layout

- ogni prodotto è assegnato a una sola posizione
- struttura semplificata (no facing avanzato)

👉 Trade-off tra realismo e complessità

---

## 🧰 Stack tecnologico

- Python
- PostgreSQL
- Docker
- SQLAlchemy
- Pandas
- Power BI
- Jupyter (solo esplorazione)

---

## 📂 Struttura del progetto

```text
RETAIL/
├── README.md
├── docker-compose.yml
├── requirements.txt
│
├── docs/
│   ├── architecture.md
│   ├── data_model.md
│   ├── pipeline.md
│   └── dashboard.md
│
├── sql/
│   ├── 01_create_schemas.sql
│   ├── 02_create_tables_core.sql
│   ├── 03_create_tables_sim.sql
│   ├── 04_create_tables_staging.sql
│   └── 05_create_tables_analytics.sql
│
├── src/
│   ├── common/
│   ├── simulation/
│   ├── ingestion/
│   ├── transform/
│   └── analytics/
│
├── scripts/
│   ├── bootstrap_db.py
│   ├── load_master_data.py
│   ├── run_simulation.py
│   └── run_pipeline.py
│
├── data/
│   ├── source/
│   └── processed/
│
└── dashboard/
```

---

## 🚀 Come eseguire il progetto

### 1. Avvio ambiente

```bash
docker compose up -d
```

### 2. Creazione schema

```bash
psql -f sql/01_create_schemas.sql
psql -f sql/02_create_tables_core.sql
psql -f sql/03_create_tables_sim.sql
psql -f sql/04_create_tables_staging.sql
```

### 3. Caricamento dati master

```bash
python -m scripts.load_products
python -m scripts.load_suppliers
python -m scripts.load_product_suppliers
```

### 4. Simulazione dati

```bash
python -m scripts.simulate_api_daily_dump --date 2026-01-01
```

### 5. Pipeline

```bash
python -m scripts.run_pipeline
```

---

## 📊 Output atteso

- dataset strutturato in `core`
- tabelle aggregate in `analytics`
- dashboard Power BI

---

## ⚠️ Limitazioni e semplificazioni

- prezzi non storicizzati
- nessuna gestione multi-store
- no real-time streaming
- fornitori semplificati
- inventory senza lotti

👉 Queste semplificazioni sono deliberate per focalizzarsi su:
- modellazione dati
- pipeline
- architettura

---

## 🔮 Possibili evoluzioni

- introduzione storico prezzi
- multi-store
- streaming (Kafka)
- orchestrazione (Airflow / Prefect)
- deploy cloud (AWS / Azure)
- data quality checks avanzati

---


---
## 🚧 Stato del progetto

- ✅ Data generation
- ✅ Data model (core / staging)
- 🚧 Data pipeline (in sviluppo)
- ⏳ Analytics layer
---

## 👨‍💻 Autore

Domenico Serino

Progetto realizzato a scopo portfolio Data Engineering