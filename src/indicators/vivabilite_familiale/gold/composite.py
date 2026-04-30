"""
Silver → Gold: Indice de vivabilité familiale (composite score)




Output:
    CSV  → data/gold/vivabilite_familiale_iris.csv
    DB   → table  vivabilite_familiale
"""
import pandas as pd

from src.config import (
    DAILY_SERVICES_SCORE_GOLD,
    ESSENTIAL_CONNECTIVITY_WEIGHTS,
    FAMILY_FACTORS_GOLD,
    GREEN_SPACES_SCORE_GOLD,
    HEALTHCARE_SCORE_GOLD,
    SCHOOL_DENSITY_GOLD,
    SERVICES_SCORE_GOLD,
    TRANSPORT_SCORE_GOLD,
    VIVABILITE_GOLD,
    VIVABILITE_WEIGHTS,
)
from src.db import engine

META_COLS = ["IRIS", "LIBCOM", "LIBIRIS", "GRD_QUART", "population", "code_iris"]
SCORE_COLS = list(VIVABILITE_WEIGHTS.keys())


def _read_gold(path, *, dtype_cols=("IRIS", "code_iris")) -> pd.DataFrame:
    dtype = {col: str for col in dtype_cols}
    df = pd.read_csv(path, dtype=dtype)
    df["IRIS"] = df["IRIS"].astype(str).str.zfill(9)
    if "code_iris" in df.columns:
        df["code_iris"] = df["code_iris"].astype(str).str.zfill(9)
    return df


def compute_vivabilite_familiale() -> pd.DataFrame:
    """
    Build the composite family liveability score from expanded Gold sub-scores.

    Reads each sub-score CSV, merges on IRIS code, applies VIVABILITE_WEIGHTS,
    and writes the result. Childcare, safety, and environment are merged from
    family factors as flat 5.0 placeholders (not weighted into vivabilite_score).

    Returns:
        DataFrame with columns:
            IRIS, code_iris, LIBCOM, LIBIRIS, GRD_QUART, population,
            school_score, childcare_score, safety_score, healthcare_score,
            environment_score, green_spaces_score, transport_score,
            daily_services_score,
            essential_connectivity_score, essential_connectivity_rank,
            vivabilite_score, vivabilite_rank
    """
    print("[vivabilite] Loading sub-scores...")

    # ── Load sub-scores ───────────────────────────────────────────────────────
    schools = _read_gold(SCHOOL_DENSITY_GOLD)
    transport = _read_gold(TRANSPORT_SCORE_GOLD)
    services = _read_gold(SERVICES_SCORE_GOLD)
    green = _read_gold(GREEN_SPACES_SCORE_GOLD)
    healthcare = _read_gold(HEALTHCARE_SCORE_GOLD)
    daily_services = _read_gold(DAILY_SERVICES_SCORE_GOLD)
    family_factors = _read_gold(FAMILY_FACTORS_GOLD)

    # ── Start with school metadata as base ───────────────────────────────────
    school_cols = [
        "school_count",
        "schools_per_1000",
        "school_score",
    ]
    base_cols = [c for c in META_COLS if c in schools.columns] + school_cols
    result = schools[base_cols].copy()

    # ── Merge other scores ────────────────────────────────────────────────────
    result = result.merge(
        transport[["IRIS", "stop_count", "weighted_stops", "transport_score"]],
        on="IRIS",
        how="left",
    )
    result = result.merge(
        services[["IRIS", "hospital_count", "service_count", "weighted_services", "services_score"]],
        on="IRIS",
        how="left",
    )
    result = result.merge(
        green[
            [
                "IRIS",
                "interior_m2",
                "adjacent_m2",
                "total_green_m2",
                "green_m2_per_resident",
                "green_spaces_score",
            ]
        ],
        on="IRIS",
        how="left",
    )
    result = result.merge(
        healthcare[
            [
                "IRIS",
                "hospital_count",
                "weighted_hospital_count",
                "healthcare_service_count",
                "weighted_healthcare_service_count",
                "weighted_healthcare_access",
                "healthcare_score",
            ]
        ].rename(columns={"hospital_count": "healthcare_hospital_count"}),
        on="IRIS",
        how="left",
    )
    result = result.merge(
        daily_services[
            [
                "IRIS",
                "daily_service_count",
                "weighted_daily_service_count",
                "daily_services_score",
            ]
        ],
        on="IRIS",
        how="left",
    )
    result = result.merge(
        family_factors[
            [
                "IRIS",
                "childcare_score",
                "safety_score",
                "environment_score",
            ]
        ],
        on="IRIS",
        how="left",
    )

    # Informative-only pillars (flat 5.0 from family factors; not in VIVABILITE_WEIGHTS).
    for col in ("childcare_score", "safety_score", "environment_score"):
        missing = result[col].isna().sum()
        if missing:
            print(f"[vivabilite]   {missing} missing values in {col} — filled with neutral 5.0")
        result[col] = result[col].fillna(5.0)

    # Fill missing sub-scores with the city-wide median (data-failure fallback).
    for col in SCORE_COLS:
        median = result[col].median()
        missing = result[col].isna().sum()
        if missing:
            print(f"[vivabilite]   {missing} missing values in {col} — filled with median {median:.2f}")
        result[col] = result[col].fillna(median)

    # ── Essential connectivity & services composite ──────────────────────────
    result["essential_connectivity_score"] = 0.0
    for col, weight in ESSENTIAL_CONNECTIVITY_WEIGHTS.items():
        result["essential_connectivity_score"] += result[col] * weight
    result["essential_connectivity_score"] = result["essential_connectivity_score"].round(2)
    result["essential_connectivity_weights"] = ";".join(
        f"{key}:{value}" for key, value in ESSENTIAL_CONNECTIVITY_WEIGHTS.items()
    )

    # ── Composite ─────────────────────────────────────────────────────────────
    result["vivabilite_score"] = 0.0
    for col, weight in VIVABILITE_WEIGHTS.items():
        result["vivabilite_score"] += result[col] * weight
    result["vivabilite_score"] = result["vivabilite_score"].round(2)

    result["vivabilite_model"] = "family_non_price_v3"
    result["vivabilite_weights"] = ";".join(
        f"{key}:{value}" for key, value in VIVABILITE_WEIGHTS.items()
    )

    # ── Rank (1 = best) ───────────────────────────────────────────────────────
    result["vivabilite_rank"] = result["vivabilite_score"].rank(
        ascending=False, method="min"
    ).astype(int)
    result["essential_connectivity_rank"] = result["essential_connectivity_score"].rank(
        ascending=False, method="min"
    ).astype(int)

    result = result.sort_values("vivabilite_rank").reset_index(drop=True)

    # ── Save ──────────────────────────────────────────────────────────────────
    VIVABILITE_GOLD.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(VIVABILITE_GOLD, index=False)
    result.to_sql("vivabilite_familiale", engine, if_exists="replace", index=False)

    print(f"[vivabilite] {len(result)} IRIS zones saved → {VIVABILITE_GOLD.name} + DB")
    print(f"  Score range: {result['vivabilite_score'].min():.2f} – {result['vivabilite_score'].max():.2f}")
    print(f"  Avg vivabilite score: {result['vivabilite_score'].mean():.2f}/10")
    print(f"  Top 5 zones:")
    for _, row in result.head(5).iterrows():
        print(f"    #{int(row['vivabilite_rank'])} {row.get('LIBIRIS', row['IRIS'])} "
              f"({row.get('LIBCOM', '')}) — {row['vivabilite_score']:.2f}")
    return result
