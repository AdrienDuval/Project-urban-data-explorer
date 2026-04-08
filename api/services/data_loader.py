"""Centralised data-loading layer.

All three silver/gold CSV files are loaded once at application startup and
stored as a ``DataStore`` dataclass that is attached to ``app.state``.
Downstream services receive the ``DataStore`` via FastAPI dependency injection
(see ``api/dependencies.py``) — they must not call ``DataStore.load()``
themselves.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

import pandas as pd

from src.config import POPULATION_SILVER, SCHOOL_DENSITY_GOLD, SCHOOLS_SILVER


def _clean_df(df: pd.DataFrame) -> pd.DataFrame:
    """Replace NaN / NaT with None so Pydantic can serialise the rows."""
    return df.where(pd.notnull(df), other=None)


@dataclass
class DataStore:
    """In-memory snapshot of the three datasets used by the API.

    Attributes:
        iris_scores:  Gold-layer DataFrame (992 rows) – one row per Paris IRIS
                      zone with school-count, schools_per_1000, and school_score.
        schools:      Silver-layer DataFrame (1 377 rows) – deduplicated school
                      catalog with lat/lng coordinates.
        population:   Silver-layer DataFrame (861 rows) – residential IRIS zones
                      with 2019 census population.
    """

    iris_scores: pd.DataFrame
    schools: pd.DataFrame
    population: pd.DataFrame

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def load(cls) -> "DataStore":
        """Read all CSVs from disk and return a populated DataStore.

        ``code_iris`` is normalised to a zero-padded 9-character string so that
        URL path parameters always match.  ``school_count`` is cast to ``int``
        (missing values become 0).
        """
        iris_scores = pd.read_csv(SCHOOL_DENSITY_GOLD, dtype={"code_iris": str})
        iris_scores["code_iris"] = iris_scores["code_iris"].str.zfill(9)
        iris_scores["school_count"] = (
            iris_scores["school_count"].fillna(0).astype(int)
        )

        schools = pd.read_csv(SCHOOLS_SILVER, dtype={"code_insee": str})

        population = pd.read_csv(POPULATION_SILVER, dtype={"IRIS": str})
        population["IRIS"] = population["IRIS"].str.zfill(9)

        return cls(
            iris_scores=_clean_df(iris_scores),
            schools=_clean_df(schools),
            population=_clean_df(population),
        )
