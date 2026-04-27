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

    def _int(key: str):
        v = _val(key)
        return int(v) if v is not None else None

    return VivabiliteIndicator(
        code_iris=str(row["IRIS"]),
        name=_val("LIBIRIS"),
        arrondissement=_val("LIBCOM"),
        population=_val("population"),
        school_count=_int("school_count"),
        schools_per_1000=_val("schools_per_1000"),
        school_score=_val("school_score"),
        childcare_score=_val("childcare_score"),
        safety_score=_val("safety_score"),
        healthcare_hospital_count=_int("healthcare_hospital_count"),
        healthcare_service_count=_int("healthcare_service_count"),
        weighted_healthcare_access=_val("weighted_healthcare_access"),
        healthcare_score=_val("healthcare_score"),
        environment_score=_val("environment_score"),
        transport_score=_val("transport_score"),
        stop_count=_int("stop_count"),
        weighted_stops=_val("weighted_stops"),
        services_score=_val("services_score"),
        daily_service_count=_int("daily_service_count"),
        weighted_daily_service_count=_val("weighted_daily_service_count"),
        daily_services_score=_val("daily_services_score"),
        interior_m2=_val("interior_m2"),
        adjacent_m2=_val("adjacent_m2"),
        total_green_m2=_val("total_green_m2"),
        green_m2_per_resident=_val("green_m2_per_resident"),
        green_spaces_score=_val("green_spaces_score"),
        vivabilite_score=_val("vivabilite_score"),
        vivabilite_rank=int(row["vivabilite_rank"]) if _val("vivabilite_rank") is not None else None,
        vivabilite_model=_val("vivabilite_model"),
        vivabilite_weights=_val("vivabilite_weights"),
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
    pages = max(1, -(-total // size))
    return PaginatedResponse(items=items, total=total, page=page, size=size, pages=pages)


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

    score_cols = [
        "school_score",
        "childcare_score",
        "safety_score",
        "healthcare_score",
        "environment_score",
        "transport_score",
        "daily_services_score",
        "green_spaces_score",
        "vivabilite_score",
    ]
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
                avg_childcare_score=round(float(group["childcare_score"].mean()), 2),
                avg_safety_score=round(float(group["safety_score"].mean()), 2),
                avg_healthcare_score=round(float(group["healthcare_score"].mean()), 2),
                avg_environment_score=round(float(group["environment_score"].mean()), 2),
                avg_transport_score=round(float(group["transport_score"].mean()), 2),
                avg_daily_services_score=round(float(group["daily_services_score"].mean()), 2),
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
