"""API-level configuration.

Data paths are inherited from ``src.config`` so there is a single source of
truth.  Only API-specific settings (metadata, CORS, etc.) live here.
"""

from __future__ import annotations

# Re-export pipeline paths so callers only need one import
from src.config import (  # noqa: F401
    POPULATION_SILVER,
    SCHOOL_DENSITY_GOLD,
    SCHOOLS_SILVER,
)

# ------------------------------------------------------------------
# FastAPI application metadata
# ------------------------------------------------------------------

API_TITLE = "Urban Data Explorer API"
API_DESCRIPTION = """
REST API exposing Paris school-accessibility indices computed from the
Bronze → Silver → Gold data pipeline.

## Data Layers

| Layer  | Content |
|--------|---------|
| **Bronze** | Raw INSEE census data, school registries, IRIS geometry |
| **Silver** | Cleaned/deduplicated IRIS zones, schools, and population |
| **Gold**   | Aggregated school-density score per IRIS zone |

## Key Concepts
 
- **IRIS zone**: The finest French census unit (~2 000 residents).
- **school_score**: A 0–100 index of how many schools (within a 500 m buffer)
  are accessible per 1 000 residents relative to the rest of Paris.
"""
API_VERSION = "0.1.0"

# Allowed CORS origins — extend for deployed frontends
CORS_ORIGINS = [
    "http://localhost",
    "http://localhost:3000",
    "http://localhost:5173",
]

