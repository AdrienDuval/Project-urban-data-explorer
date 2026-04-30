"""Legacy data-loading layer — now only used for bdcom/dvf CSV fallback.

All other datasets are served from MySQL via service functions.
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd


def _clean_df(df: pd.DataFrame) -> pd.DataFrame:
    """Replace NaN/NaT with None so Pydantic can serialise the rows."""
    return df.where(pd.notnull(df), other=None)


@dataclass
class DataStore:
    """Minimal stub kept for bdcom/dvf services."""

    bdcom_scores: pd.DataFrame = field(default_factory=pd.DataFrame)
    dvf_scores: pd.DataFrame = field(default_factory=pd.DataFrame)

    @classmethod
    def load(cls) -> "DataStore":
        return cls()
