"""Business logic for the family liveability indicator (vivabilité familiale).

Reads the Gold composite CSV loaded into DataStore and serves the
VivabiliteIndicator and VivabiliteArrondissementStats response models.
"""

from __future__ import annotations

from typing import List, Optional

import pandas as pd

from api.models.common import PaginatedResponse
from api.models.indicators.vivabilite import (
    VivabiliteArrondissementStats,
    VivabiliteIndicator,
)
from api.services.data_loader import DataStore


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _row_to_indicator(row: pd.Series) -> VivabiliteIndicator:
    def _val(key: str):
        v = row.get(key)
        return None if v is None or (isinstance(v, float) and pd.isna(v)) else v

    return VivabiliteIndicator(
        code_iris=str(row["IRIS"]),
        name=_val("LIBIRIS"),
        arrondissement=_val("LIBCOM"),
        population=_val("population"),
        school_score=_val("school_score"),
        transport_score=_val("transport_score"),
        services_score=_val("services_score"),
        green_spaces_score=_val("green_spaces_score"),
        vivabilite_score=_val("vivabilite_score"),
        vivabilite_rank=int(row["vivabilite_rank"]) if _val("vivabilite_rank") is not None else None,
    )


def _paginate(df: pd.DataFrame, page: int, size: int) -> tuple[pd.DataFrame, int]:
    total = len(df)
    return df.iloc[(page - 1) * size : page * size], total


# ---------------------------------------------------------------------------
# Public service functions
# ---------------------------------------------------------------------------

def list_vivabilite_indicators(
    store: DataStore,
    *,
    arrondissement: Optional[str] = None,
    min_score: Optional[float] = None,
    max_score: Optional[float] = None,
    page: int = 1,
    size: int = 50,
) -> PaginatedResponse[VivabiliteIndicator]:
    df = store.vivabilite_scores.copy()

    if arrondissement:
        mask = df["LIBCOM"].astype(str).str.lower().str.contains(
            arrondissement.lower(), na=False
        )
        df = df[mask]

    if min_score is not None:
        df = df[df["vivabilite_score"] >= min_score]
    if max_score is not None:
        df = df[df["vivabilite_score"] <= max_score]

    df = df.sort_values("vivabilite_rank", na_position="last")
    page_df, total = _paginate(df, page, size)
    items = [_row_to_indicator(row) for _, row in page_df.iterrows()]
    return PaginatedResponse(items=items, total=total, page=page, size=size)


def get_vivabilite_indicator(
    store: DataStore, code_iris: str
) -> Optional[VivabiliteIndicator]:
    df = store.vivabilite_scores
    match = df[df["IRIS"].astype(str).str.zfill(9) == code_iris.zfill(9)]
    if match.empty:
        return None
    return _row_to_indicator(match.iloc[0])


def list_vivabilite_arrondissements(
    store: DataStore,
) -> List[VivabiliteArrondissementStats]:
    df = store.vivabilite_scores.copy()
    df = df[df["LIBCOM"].notna() & (df["LIBCOM"].astype(str) != "nan")]

    score_cols = ["school_score", "transport_score", "services_score", "green_spaces_score", "vivabilite_score"]
    for col in score_cols:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    grouped = df.groupby("LIBCOM")
    results = []
    for arrdt, group in grouped:
        best_row = group.loc[group["vivabilite_score"].idxmax()] if not group["vivabilite_score"].isna().all() else None
        results.append(
            VivabiliteArrondissementStats(
                arrondissement=arrdt,
                iris_count=len(group),
                total_population=float(group["population"].sum()),
                avg_school_score=round(float(group["school_score"].mean()), 2),
                avg_transport_score=round(float(group["transport_score"].mean()), 2),
                avg_services_score=round(float(group["services_score"].mean()), 2),
                avg_green_spaces_score=round(float(group["green_spaces_score"].mean()), 2),
                avg_vivabilite_score=round(float(group["vivabilite_score"].mean()), 2),
                best_iris=str(best_row["LIBIRIS"]) if best_row is not None and pd.notna(best_row.get("LIBIRIS")) else None,
            )
        )

    return sorted(results, key=lambda x: x.arrondissement)


def get_vivabilite_arrondissement(
    store: DataStore, arrondissement: str
) -> Optional[VivabiliteArrondissementStats]:
    all_stats = list_vivabilite_arrondissements(store)
    for stat in all_stats:
        if arrondissement.lower() in stat.arrondissement.lower():
            return stat
    return None
