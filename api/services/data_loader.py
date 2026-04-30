"""Legacy data-loading layer — now only used for bdcom/dvf CSV fallback.

All other datasets are served from MySQL via the service functions in
api/services/*.  Spatial GeoDataFrames are served from api/services/spatial_cache.py.

bdcom and dvf do not yet have MySQL tables; their services return empty data
until the pipeline populates them.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


def _clean_df(df: pd.DataFrame) -> pd.DataFrame:
    """Replace NaN/NaT with None so Pydantic can serialise the rows."""
    return df.where(pd.notnull(df), other=None)


@dataclass
class DataStore:
    """Minimal stub kept for bdcom/dvf routers that still reference DataStoreDep.

    All fields default to empty DataFrames — bdcom and dvf are unavailable
    until their MySQL tables are created by the pipeline.
    """

    bdcom_scores: pd.DataFrame = field(default_factory=pd.DataFrame)
    dvf_scores: pd.DataFrame = field(default_factory=pd.DataFrame)

    @classmethod
    def load(cls) -> "DataStore":
        return cls()
