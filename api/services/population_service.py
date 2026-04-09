"""Business logic for population queries."""

from __future__ import annotations

from typing import Optional

import pandas as pd

from api.models.common import PaginatedResponse
from api.models.population import PopulationZone
from api.services.data_loader import DataStore


def _row_to_zone(row: pd.Series) -> PopulationZone:
    return PopulationZone(
        code_iris=str(row["IRIS"]).zfill(9),
        arrondissement=str(row.get("LIBCOM", "")),
        name=str(row.get("LIBIRIS", row.get("LAB_IRIS", ""))),
        quarter_code=str(row.get("GRD_QUART", "")),
        population=float(row["population"]),
    )


def _enrich_population(store: DataStore) -> pd.DataFrame:
    """Join population silver with iris_scores gold to add LIBCOM/LIBIRIS/GRD_QUART."""
    pop = store.population.copy()
    pop["IRIS"] = pop["IRIS"].astype(str).str.zfill(9)
    if store.iris_scores.empty:
        return pop
    meta = store.iris_scores[["code_iris", "LIBCOM", "LIBIRIS", "GRD_QUART"]].copy()
    meta = meta.rename(columns={"code_iris": "IRIS"})
    return pop.merge(meta, on="IRIS", how="left")


def _paginate(df: pd.DataFrame, page: int, size: int) -> tuple[pd.DataFrame, int]:
    total = len(df)
    return df.iloc[(page - 1) * size : page * size], total


def list_population_zones(
    store: DataStore,
    *,
    arrondissement: Optional[str] = None,
    page: int = 1,
    size: int = 50,
) -> PaginatedResponse[PopulationZone]:
    """Return a paginated list of residential IRIS zones with census population.

    Args:
        store:          Loaded DataStore.
        arrondissement: Partial, case-insensitive match against the LIBCOM
                        column (e.g. ``"7e"``).
        page:           1-based page number.
        size:           Page size (max enforced by the router).
    """
    df = _enrich_population(store)

    if arrondissement:
        df = df[df["LIBCOM"].str.contains(arrondissement, case=False, na=False)]

    page_df, total = _paginate(df, page, size)
    pages = max(1, -(-total // size))

    return PaginatedResponse(
        items=[_row_to_zone(row) for _, row in page_df.iterrows()],
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


def get_population_zone(
    store: DataStore, code_iris: str
) -> Optional[PopulationZone]:
    """Fetch population data for a single IRIS zone by its 9-digit code.

    Returns ``None`` when the code is not found in the residential dataset.
    """
    code_iris = code_iris.zfill(9)
    df = _enrich_population(store)
    matches = df[df["IRIS"] == code_iris]
    if matches.empty:
        return None
    return _row_to_zone(matches.iloc[0])
