"""Centralised data-loading layer.

All three silver/gold CSV files are loaded once at application startup and
stored as a ``DataStore`` dataclass that is attached to ``app.state``.
Downstream services receive the ``DataStore`` via FastAPI dependency injection
(see ``api/dependencies.py``) — they must not call ``DataStore.load()``
themselves.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from typing import Any

import pandas as pd

from src.config import (
    IRIS_GEOJSON,
    POPULATION_SILVER,
    SCHOOL_DENSITY_GOLD,
    SCHOOLS_SILVER,
    TRANSPORT_INDICATOR_GOLD,
    TRANSPORT_POINTS_GOLD,
    VIVABILITE_GOLD,
)


def _clean_df(df: pd.DataFrame) -> pd.DataFrame:
    """Replace NaN / NaT with None so Pydantic can serialise the rows."""
    return df.where(pd.notnull(df), other=None)


@dataclass
class DataStore:
    """In-memory snapshot of all datasets used by the API.

    Attributes:
        iris_scores:  Gold-layer DataFrame (992 rows) – one row per Paris IRIS
            zone with school-count, schools_per_1000, and school_score.
        schools:      Silver-layer DataFrame (1 377 rows) – deduplicated school
            catalog with lat/lng coordinates.
        population:   Silver-layer DataFrame (861 rows) – residential IRIS zones
            with 2019 census population.
        vivabilite_scores: Gold composite family-liveability score per IRIS.
    """

    iris_scores: pd.DataFrame
    schools: pd.DataFrame
    population: pd.DataFrame
    vivabilite_scores: pd.DataFrame
    transport_scores: pd.DataFrame
    transport_points: pd.DataFrame
    iris_geojson: dict[str, Any]

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def load(cls) -> "DataStore":
        """Read all CSVs from disk and return a populated DataStore.

        ``code_iris`` is normalised to a zero-padded 9-character string so that
        URL path parameters always match.  ``school_count`` is cast to ``int``
        (missing values become 0).

        Missing files produce an empty DataFrame with a warning instead of
        crashing the API — useful when the pipeline hasn't been run yet.
        """
        import logging
        logger = logging.getLogger(__name__)

        if IRIS_GEOJSON.exists():
            logger.info("Loading geometry: %s", IRIS_GEOJSON.name)
            with IRIS_GEOJSON.open(encoding="utf-8") as fh:
                iris_geojson = json.load(fh)
            logger.info("  → %d IRIS geometries loaded", len(iris_geojson.get("features", [])))
        else:
            logger.warning("IRIS GeoJSON not found: %s — run `python run_pipeline.py`", IRIS_GEOJSON)
            iris_geojson = {"type": "FeatureCollection", "features": []}

        if SCHOOL_DENSITY_GOLD.exists():
            logger.info("Loading gold: %s", SCHOOL_DENSITY_GOLD.name)
            iris_scores = pd.read_csv(SCHOOL_DENSITY_GOLD, dtype={"code_iris": str})
            iris_scores["code_iris"] = iris_scores["code_iris"].str.zfill(9)
            iris_scores["school_count"] = iris_scores["school_count"].fillna(0).astype(int)
            logger.info("  → %d IRIS zones loaded", len(iris_scores))
        else:
            logger.warning("Gold file not found: %s — run `python run_pipeline.py`", SCHOOL_DENSITY_GOLD)
            iris_scores = pd.DataFrame()

        if SCHOOLS_SILVER.exists():
            logger.info("Loading silver: %s", SCHOOLS_SILVER.name)
            schools = pd.read_csv(SCHOOLS_SILVER, dtype={"code_insee": str})
            logger.info("  → %d schools loaded", len(schools))
        else:
            logger.warning("Silver file not found: %s — run `python run_pipeline.py`", SCHOOLS_SILVER)
            schools = pd.DataFrame()

        if POPULATION_SILVER.exists():
            logger.info("Loading silver: %s", POPULATION_SILVER.name)
            population = pd.read_csv(POPULATION_SILVER, dtype={"IRIS": str})
            population["IRIS"] = population["IRIS"].str.zfill(9)
            logger.info("  → %d population zones loaded", len(population))
        else:
            logger.warning("Silver file not found: %s — run `python run_pipeline.py`", POPULATION_SILVER)
            population = pd.DataFrame()
        
        if TRANSPORT_INDICATOR_GOLD.exists():
            transport_scores = pd.read_csv(TRANSPORT_INDICATOR_GOLD, dtype={"CODE_IRIS": str})
            transport_scores["CODE_IRIS"] = transport_scores["CODE_IRIS"].str.zfill(9)
        else:
            transport_scores = pd.DataFrame()

        if TRANSPORT_POINTS_GOLD.exists():
            transport_points = pd.read_csv(TRANSPORT_POINTS_GOLD, dtype={"id": str})
        else:
            transport_points = pd.DataFrame()

        if VIVABILITE_GOLD.exists():
            logger.info("Loading gold: %s", VIVABILITE_GOLD.name)
            vivabilite_scores = pd.read_csv(VIVABILITE_GOLD, dtype={"IRIS": str, "code_iris": str})
            vivabilite_scores["IRIS"] = vivabilite_scores["IRIS"].str.zfill(9)
            logger.info("  → %d IRIS zones loaded", len(vivabilite_scores))
        else:
            logger.warning("Gold file not found: %s — run `python run_pipeline.py`", VIVABILITE_GOLD)
            vivabilite_scores = pd.DataFrame()

        return cls(
            iris_scores=_clean_df(iris_scores),
            schools=_clean_df(schools),
            population=_clean_df(population),
            vivabilite_scores=_clean_df(vivabilite_scores),
            transport_scores=_clean_df(transport_scores),
            transport_points=_clean_df(transport_points),
            iris_geojson=iris_geojson,
        )
