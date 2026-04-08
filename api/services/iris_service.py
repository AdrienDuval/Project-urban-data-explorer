"""Business logic for IRIS administrative zone queries.

Returns *only* geographic / administrative metadata (code, name, quarter,
arrondissement).  Population data is in ``population_service``.
Indicator results are in ``services/indicators/``.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd

from api.models.common import PaginatedResponse
from api.models.iris import IrisZone
from api.services.data_loader import DataStore


def _row_to_iris_zone(row: pd.Series) -> IrisZone:
    """Convert a ``iris_scores`` row into a pure-admin ``IrisZone``."""
    return IrisZone(
        code_iris=str(row["code_iris"]),
        name=row["LIBIRIS"] if pd.notna(row.get("LIBIRIS")) else None,
        quarter_code=(
            str(int(row["GRD_QUART"])) if pd.notna(row.get("GRD_QUART")) else None
        ),
        arrondissement=row["LIBCOM"] if pd.notna(row.get("LIBCOM")) else None,
    )


def _paginate(df: pd.DataFrame, page: int, size: int) -> tuple[pd.DataFrame, int]:
    total = len(df)
    return df.iloc[(page - 1) * size : page * size], total


def list_iris_zones(
    store: DataStore,
    *,
    arrondissement: Optional[str] = None,
    page: int = 1,
    size: int = 50,
) -> PaginatedResponse[IrisZone]:
    """Return a paginated list of IRIS zones (administrative metadata only).

    Args:
        store:          Loaded DataStore.
        arrondissement: Partial, case-insensitive match on the arrondissement
                        name (e.g. ``"7e"`` matches ``"Paris 7e Arrondissement"``).
        page:           1-based page number.
        size:           Page size (max enforced by the router).
    """
    df = store.iris_scores[["code_iris", "LIBIRIS", "GRD_QUART", "LIBCOM"]].copy()

    if arrondissement:
        df = df[df["LIBCOM"].str.contains(arrondissement, case=False, na=False)]

    page_df, total = _paginate(df, page, size)
    pages = max(1, -(-total // size))

    return PaginatedResponse(
        items=[_row_to_iris_zone(row) for _, row in page_df.iterrows()],
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


def get_iris_zone(store: DataStore, code_iris: str) -> Optional[IrisZone]:
    """Fetch administrative metadata for a single IRIS zone by its 9-digit code.

    Returns ``None`` when the code is not found (the router raises 404).
    """
    code_iris = code_iris.zfill(9)
    matches = store.iris_scores[store.iris_scores["code_iris"] == code_iris]
    if matches.empty:
        return None
    return _row_to_iris_zone(matches.iloc[0])
