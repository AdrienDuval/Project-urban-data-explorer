# Urban Data Explorer

Paris housing dynamics dashboard — EFREI M1 group project.
Reveals hidden housing truths in Paris (price/m², social housing, school accessibility, transport) through an interactive map with a Bronze/Silver/Gold data pipeline and a FastAPI backend.

---

## Architecture — Medallion pattern

```
BRONZE (files only)              SILVER (files only)             GOLD (files + DB)
────────────────────             ──────────────────────          ─────────────────────────────
iris.xlsx               →        iris_paris.csv
base-ic-evol-pop.CSV    →        population_paris.csv    ──┐
schools/*.xlsx          →        schools_merged.csv      ──┼──→  schools_ref        (DB)
                                                           └──→  population_ref     (DB)
ValeursFoncieres.txt    →        dvf_paris_clean.csv     ──→  (DVF Gold indicator — todo)
BDCOM_2023.csv          →        bdcom_paris_clean.csv   ──→  (BDCOM Gold indicator — todo)
hospitals.csv           →        hospitals_paris.csv     ──→  (hospital indicator — todo)
                                 iris.geojson (bronze)   ──┐
                                 schools_merged.csv      ──┼──→  school_density     (DB + CSV)
                                 population_paris.csv    ──┘
```

**Rule:** Bronze = raw. Silver = cleaned files, never in DB. Gold = computed indicators and reference tables, always in DB.

## Project structure

```
api/                        FastAPI backend
├── config.py               API title, version, CORS origins
├── dependencies.py         Shared FastAPI dependencies
├── main.py                 App factory, routers registration
├── models/                 Pydantic response schemas
└── routers/                Route handlers
    ├── iris.py             GET /iris
    ├── population.py       GET /population
    ├── schools.py          GET /schools
    ├── stats.py            GET /stats
    └── indicators/
        └── schools.py      GET /indicators/schools

src/                        Data pipeline
├── config.py               All file paths & pipeline constants
├── data_loader.py          Downloads Bronze subfolders from Google Drive
├── db.py                   Shared MySQL engine — reads credentials from .env
├── silver/                 Bronze → Silver: clean & filter, output CSV files only
│   ├── iris.py             → iris_paris.csv
│   ├── population.py       → population_paris.csv
│   ├── schools.py          → schools_merged.csv
│   ├── dvf.py              → dvf_paris_clean.csv
│   ├── bdcom.py            → bdcom_paris_clean.csv
│   └── hospitals.py        → hospitals_paris.csv
└── gold/                   Silver → Gold: compute indicators, write CSV + DB
    ├── reference.py        Promotes schools + population to DB (map layers)
    └── school_density.py   School accessibility score per IRIS zone

data/
├── bronze/                 Raw input files — gitignored, downloaded from Drive
├── silver/                 Cleaned CSVs — gitignored, never in DB
└── gold/                   Indicator CSVs — committed to Git + written to DB

exploration/                Jupyter notebooks (EDA, prototyping)
run_pipeline.py             Pipeline entry point
```

---

## Setup

### 1. Install dependencies

```bash
pip install -r requirements.txt
```

### 2. Get the `.env` file

Ask a teammate. It contains the shared MySQL credentials and must never be committed.
Place it at the project root. It looks like:

```
DB_HOST=srv900.hstgr.io
DB_PORT=3306
DB_NAME=u387197059_urban_project
DB_USER=your_user
DB_PASSWORD=your_password
```

---

## Running the data pipeline

```bash
# Full pipeline: download Bronze → Silver → Gold → write to DB
python run_pipeline.py

# Silver layer only (clean raw files, no DB writes)
python run_pipeline.py --silver

# Gold layer only (compute indicators + write to DB, requires Silver to exist)
python run_pipeline.py --gold
```

The first full run downloads ~700 MB of raw data from Google Drive into `data/bronze/`.
Subsequent runs skip the download if Bronze already exists (use `force_update=True` in code to re-download).

### What gets written to the database

The DB is only written during the **Gold step**. Silver stays as local files only.

| DB Table | Script | Content | Why in Gold |
|----------|--------|---------|-------------|
| `schools_ref` | `gold/reference.py` | School points with lat/lng | Needed for Mapbox point markers |
| `population_ref` | `gold/reference.py` | Population per IRIS zone | Needed for choropleth layer |
| `school_density` | `gold/school_density.py` | School accessibility score per IRIS | Core computed indicator |

Each teammate's Gold indicator will add its own table here (e.g. `dvf_score_iris`, `hospital_score_iris`).

---

## Running the API

> **Important:** always use the venv's uvicorn, not a system-wide one.
> If `uvicorn` resolves to a different Python environment (e.g. miniconda), the wrong packages will load and the API will crash.

```bash
# Recommended — activate venv first, then run
source .venv/Scripts/activate
uvicorn api.main:app --reload

# Or call it directly without activating
.venv/Scripts/uvicorn api.main:app --reload
```

Server starts at `http://127.0.0.1:8000`.

| URL | Description |
|-----|-------------|
| `http://127.0.0.1:8000/docs` | Swagger UI — interactive endpoint explorer |
| `http://127.0.0.1:8000/redoc` | ReDoc documentation |
| `http://127.0.0.1:8000/health` | Health check — confirms datasets are loaded |

### Available endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/iris` | Paginated list of Paris IRIS zones, filterable by arrondissement |
| GET | `/iris/{code_iris}` | Single IRIS zone by 9-digit INSEE code |
| GET | `/population` | Population data per IRIS zone |
| GET | `/schools` | School list with coordinates |
| GET | `/indicators/schools` | School accessibility score per IRIS zone |
| GET | `/map/vivabilite-familiale` | GeoJSON IRIS polygons enriched with family liveability scores |
| GET | `/stats` | Aggregate statistics |

---

## Running the interactive map

The Next.js frontend lives in `web/` and consumes the FastAPI backend.

```bash
cd web
cp .env.example .env.local
npm install
npm run dev
```

Required frontend environment variables:

```bash
NEXT_PUBLIC_API_URL=http://127.0.0.1:8000
NEXT_PUBLIC_MAPBOX_TOKEN=your_mapbox_token
```

If `NEXT_PUBLIC_MAPBOX_TOKEN` is empty, the map falls back to a public
Mapbox-compatible basemap style. Start the API first with the project venv:

```bash
.venv/Scripts/uvicorn api.main:app --reload
```

The vivability choropleth requires the Gold output
`data/gold/vivabilite_familiale_iris.csv`. Generate it with:

```bash
python run_pipeline.py --gold
```

---

## Team guide — working together

### First-time setup (do this once)

```bash
git clone <repo-url>
cd Project-urban-data-explorer
python -m venv .venv
source .venv/Scripts/activate        # Windows Git Bash
# source .venv/bin/activate          # Mac/Linux
pip install -r requirements.txt
# Place the .env file at the project root (get it from a teammate)
python run_pipeline.py               # downloads data, runs pipeline, writes Gold to DB
```

### Daily workflow

```bash
git pull                            # get teammates' latest indicator code
python run_pipeline.py --gold       # recompute all Gold indicators → writes to shared DB
```

No data files to commit — the DB is updated automatically when you run the pipeline.

### Adding a new Gold indicator

1. Create `src/gold/your_indicator.py` — model it after [src/gold/school_density.py](src/gold/school_density.py)
2. Add your output path to [src/config.py](src/config.py)
3. End your compute function with both a CSV save and a DB write:

```python
from src.db import engine

result.to_csv(YOUR_GOLD_PATH, index=False)
result.to_sql("your_indicator", engine, if_exists="replace", index=False)
```

4. Call your function inside `run_gold()` in [run_pipeline.py](run_pipeline.py)

### What goes where

| Layer | Storage | DB? | Committed to Git? |
|-------|---------|-----|-------------------|
| Bronze | `data/bronze/` — raw files from Google Drive | No | No |
| Silver | `data/silver/` — cleaned CSVs | No | No |
| Gold | `data/gold/` — computed indicator CSVs | Yes | No — DB is the source of truth |
| `.env` | Project root — DB credentials | — | **Never** |

> The entire `data/` folder is gitignored. Everyone downloads Bronze from Drive and regenerates Silver and Gold locally by running the pipeline. The shared DB is the single source of truth for Gold data — no CSV commits needed.

### Browsing the database from VS Code

Install the **Database Client** extension (`cweijan.vscode-mysql-client2`) from the VS Code marketplace.

Create a new connection with these values (from the `.env` file):

| Field | Value |
|-------|-------|
| Host | `srv900.hstgr.io` |
| Port | `3306` |
| User | `u387197059_urban_efrei_m1` |
| Password | *(ask a teammate — same as `.env`)* |
| Database | `u387197059_urban_project` |

> **Hostinger remote access:** before connecting, go to hPanel → Databases → Remote MySQL → add your IP address (or `%` to allow any IP during development). Without this, the connection will be refused.

### The `src/db.py` module

All DB writes go through a single shared engine defined in [src/db.py](src/db.py).
It reads credentials from `.env` at startup using `python-dotenv`.

```python
from src.db import engine

# Write a DataFrame to the DB (replace table on each run)
df.to_sql("your_table_name", engine, if_exists="replace", index=False)
```

Never import `engine` in Silver scripts — only Gold scripts write to the DB.
