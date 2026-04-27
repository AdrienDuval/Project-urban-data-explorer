"""
Silver → Gold: Indice de vivabilité familiale (composite score)

Combines four sub-indicators into a single 0–10 family liveability score
for each Paris IRIS zone:

    vivabilite = (school_score × 0.25)
               + (transport_score × 0.25)
               + (services_score × 0.25)
               + (green_spaces_score × 0.25)

Each sub-score is already normalised 0–10 by its own Gold script, so the
composite is also on the same 0–10 scale without further normalisation.

A rank (1 = best zone in Paris) is also computed and stored.

Output:
    CSV  → data/gold/vivabilite_familiale_iris.csv
    DB   → table  vivabilite_familiale
"""
import pandas as pd

from src.config import (
    GREEN_SPACES_SCORE_GOLD,
    SCHOOL_DENSITY_GOLD,
    SERVICES_SCORE_GOLD,
    TRANSPORT_SCORE_GOLD,
    VIVABILITE_GOLD,
    VIVABILITE_WEIGHTS,
)
from src.db import engine

# Columns to carry over from sub-score files (metadata only, no duplication)
META_COLS = ["IRIS", "LIBCOM", "LIBIRIS", "GRD_QUART", "population", "code_iris"]


def compute_vivabilite_familiale() -> pd.DataFrame:
    """
    Build the composite family liveability score from the four Gold sub-scores.

    Reads each sub-score CSV, merges on IRIS code, applies VIVABILITE_WEIGHTS,
    and writes the result.

    Returns:
        DataFrame with columns:
            IRIS, code_iris, LIBCOM, LIBIRIS, GRD_QUART, population,
            school_score, transport_score, services_score, green_spaces_score,
            vivabilite_score, vivabilite_rank
    """
    print("[vivabilite] Loading sub-scores...")

    # ── Load sub-scores ───────────────────────────────────────────────────────
    schools = pd.read_csv(SCHOOL_DENSITY_GOLD, dtype={"IRIS": str, "code_iris": str})
    schools["IRIS"] = schools["IRIS"].str.zfill(9)
    # Normalise schools_per_1000 to 0–10 as school_score (not yet in that file)
    mn, mx = schools["schools_per_1000"].min(), schools["schools_per_1000"].max()
    if mx > mn:
        schools["school_score"] = ((schools["schools_per_1000"] - mn) / (mx - mn) * 10).round(2)
    else:
        schools["school_score"] = 5.0

    transport = pd.read_csv(TRANSPORT_SCORE_GOLD, dtype={"IRIS": str, "code_iris": str})
    transport["IRIS"] = transport["IRIS"].str.zfill(9)

    services = pd.read_csv(SERVICES_SCORE_GOLD, dtype={"IRIS": str, "code_iris": str})
    services["IRIS"] = services["IRIS"].str.zfill(9)

    green = pd.read_csv(GREEN_SPACES_SCORE_GOLD, dtype={"IRIS": str, "code_iris": str})
    green["IRIS"] = green["IRIS"].str.zfill(9)

    # ── Start with school metadata as base ───────────────────────────────────
    base_cols = [c for c in META_COLS if c in schools.columns] + ["school_score"]
    result = schools[base_cols].copy()

    # ── Merge other scores ────────────────────────────────────────────────────
    result = result.merge(
        transport[["IRIS", "transport_score"]], on="IRIS", how="left"
    )
    result = result.merge(
        services[["IRIS", "services_score"]], on="IRIS", how="left"
    )
    result = result.merge(
        green[["IRIS", "green_spaces_score"]], on="IRIS", how="left"
    )

    # Fill any missing sub-scores with the city-wide median (graceful fallback)
    for col in ["school_score", "transport_score", "services_score", "green_spaces_score"]:
        median = result[col].median()
        missing = result[col].isna().sum()
        if missing:
            print(f"[vivabilite]   {missing} missing values in {col} — filled with median {median:.2f}")
        result[col] = result[col].fillna(median)

    # ── Composite ─────────────────────────────────────────────────────────────
    result["vivabilite_score"] = (
        result["school_score"]       * VIVABILITE_WEIGHTS["school_score"]
        + result["transport_score"]  * VIVABILITE_WEIGHTS["transport_score"]
        + result["services_score"]   * VIVABILITE_WEIGHTS["services_score"]
        + result["green_spaces_score"] * VIVABILITE_WEIGHTS["green_spaces_score"]
    ).round(2)

    # ── Rank (1 = best) ───────────────────────────────────────────────────────
    result["vivabilite_rank"] = result["vivabilite_score"].rank(
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
