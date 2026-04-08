"""Business logic for the school-accessibility indicator.

Combines the gold-layer ``iris_scores`` DataFrame (school counts and scores)
with IRIS administrative metadata and census population to produce the
``SchoolIndicator`` response model.
"""

from __future__ import annotations

from typing import Optional

import pandas as pd

from api.models.common import PaginatedResponse
from api.models.indicators.schools import SchoolArrondissementStats, SchoolIndicator
from api.services.data_loader import DataStore


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _row_to_indicator(row: pd.Series) -> SchoolIndicator:
    """Convert a ``iris_scores`` row into a ``SchoolIndicator``."""
    return SchoolIndicator(
        code_iris=str(row["code_iris"]),
        name=row["LIBIRIS"] if pd.notna(row.get("LIBIRIS")) else None,
        quarter_code=(
            str(int(row["GRD_QUART"])) if pd.notna(row.get("GRD_QUART")) else None
        ),
        arrondissement=row["LIBCOM"] if pd.notna(row.get("LIBCOM")) else None,
        population=row["population"] if pd.notna(row.get("population")) else None,
        school_count=int(row["school_count"]),
        schools_per_1000=(
            row["schools_per_1000"] if pd.notna(row.get("schools_per_1000")) else None
        ),
        school_score=(
            row["school_score"] if pd.notna(row.get("school_score")) else None
        ),
    )


def _paginate(df: pd.DataFrame, page: int, size: int) -> tuple[pd.DataFrame, int]:
    total = len(df)
    return df.iloc[(page - 1) * size : page * size], total


# ---------------------------------------------------------------------------
# Public service functions
# ---------------------------------------------------------------------------

def list_school_indicators(
    store: DataStore,
    *,
    arrondissement: Optional[str] = None,
    min_score: Optional[float] = None,
    max_score: Optional[float] = None,
    page: int = 1,
    size: int = 50,
) -> PaginatedResponse[SchoolIndicator]:
    """Return a paginated list of school-accessibility scores per IRIS zone.

    Args:
        store:          Loaded DataStore.
        arrondissement: Partial, case-insensitive match on the arrondissement
                        name (e.g. ``"7e"``).
        min_score:      Include only zones with school_score ≥ this value.
        max_score:      Include only zones with school_score ≤ this value.
        page:           1-based page number.
        size:           Page size (max enforced by the router).
    """
    df = store.iris_scores.copy()

    if arrondissement:
        df = df[df["LIBCOM"].str.contains(arrondissement, case=False, na=False)]

    if min_score is not None:
        df = df[df["school_score"].notna() & (df["school_score"] >= min_score)]

    if max_score is not None:
        df = df[df["school_score"].notna() & (df["school_score"] <= max_score)]

    page_df, total = _paginate(df, page, size)
    pages = max(1, -(-total // size))

    return PaginatedResponse(
        items=[_row_to_indicator(row) for _, row in page_df.iterrows()],
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


def get_school_indicator(
    store: DataStore, code_iris: str
) -> Optional[SchoolIndicator]:
    """Fetch school-accessibility data for a single IRIS zone.

    Returns ``None`` when the code is not found (router raises 404).
    """
    code_iris = code_iris.zfill(9)
    matches = store.iris_scores[store.iris_scores["code_iris"] == code_iris]
    if matches.empty:
        return None
    return _row_to_indicator(matches.iloc[0])


def list_school_arrondissements(
    store: DataStore,
) -> list[SchoolArrondissementStats]:
    """Aggregate school-accessibility metrics by arrondissement.

    Only residential zones (non-null population, LIBCOM, and school_score) are
    included so that per-1 000 metrics are meaningful.
    """
    df = store.iris_scores.dropna(subset=["LIBCOM", "population", "school_score"])

    results: list[SchoolArrondissementStats] = []
    for arrond, group in df.groupby("LIBCOM"):
        total_pop = group["population"].sum()
        total_schools = group["school_count"].sum()
        weighted = (group["schools_per_1000"] * group["population"]).sum()
        avg_per_1000 = round(weighted / total_pop, 4) if total_pop > 0 else 0.0

        results.append(
            SchoolArrondissementStats(
                arrondissement=str(arrond),
                iris_count=len(group),
                total_population=round(total_pop, 2),
                total_schools=int(total_schools),
                avg_schools_per_1000=avg_per_1000,
                avg_school_score=round(float(group["school_score"].mean()), 4),
            )
        )

    results.sort(key=lambda x: x.arrondissement)
    return results


def get_school_arrondissement(
    store: DataStore, arrondissement: str
) -> Optional[SchoolArrondissementStats]:
    """Return stats for a single arrondissement (case-insensitive partial match).

    Returns ``None`` when nothing matches (router raises 404).
    """
    query = arrondissement.lower()
    matches = [
        s for s in list_school_arrondissements(store)
        if query in s.arrondissement.lower()
    ]
    return matches[0] if matches else None
