# Urban Data Explorer

Paris school-accessibility index built on INSEE IRIS census data and official school registries.

## Running the API

### With the convenience script

```bash
python run_api.py
```

### Directly with uvicorn

```bash
uvicorn api.main:app --reload --host 127.0.0.1 --port 8000
```

Both start the server at `http://127.0.0.1:8000`.

| URL | Description |
|-----|-------------|
| `http://127.0.0.1:8000/docs` | Swagger UI (interactive) |
| `http://127.0.0.1:8000/redoc` | ReDoc documentation |

### Production

Remove `--reload` and set the number of workers:

```bash
uvicorn api.main:app --workers 4 --host 0.0.0.0 --port 8000
```

## Running the data pipeline

```bash
# Full pipeline (silver + gold)
python run_pipeline.py

# Silver layer only
python run_pipeline.py --silver

# Gold layer only
python run_pipeline.py --gold
```

## Project structure

```
api/                   FastAPI backend
├── models/            Pydantic response schemas
├── routers/           Route handlers (/iris, /schools, /stats)
└── services/          Business logic and data loading

src/                   Data pipeline
├── silver/            Bronze → Silver transformations
└── gold/              Silver → Gold aggregations

data/
├── bronze/            Raw input files (INSEE, school registries)
├── silver/            Cleaned IRIS zones, schools, population
└── gold/              Final school-accessibility scores per IRIS zone

exploration/           Jupyter notebooks
```

## Setup

```bash
pip install -r requirements.txt
```
