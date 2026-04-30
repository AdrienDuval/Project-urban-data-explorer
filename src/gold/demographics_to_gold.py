"""
Gold layer — indicateurs démographiques et socio-économiques normalisés.
Produit :
  - score_revenus       (0-10) : revenu médian normalisé
  - score_mixite        (0-10) : indice de mixité sociale (entropie des CSP)
  - score_seniors       (0-10) : part de population 65+
  - demographics_score  (0-10) : score composite
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from src.config import DEMO_SILVER, DEMO_GOLD
from src.db import engine



def _robust_score(series: pd.Series, cap_percentile: int = 95,
                  higher_is_better: bool = True) -> pd.Series:
    """Normalisation robuste 0-10 avec capping au percentile."""
    values = pd.to_numeric(series, errors="coerce")
    cap = np.percentile(values.dropna(), cap_percentile)
    floor = np.percentile(values.dropna(), 100 - cap_percentile)
    clipped = values.clip(lower=floor, upper=cap)
    mn, mx = clipped.min(), clipped.max()
    if mx == mn:
        return pd.Series(5.0, index=series.index)
    scaled = (clipped - mn) / (mx - mn) * 10
    if not higher_is_better:
        scaled = 10 - scaled
    return scaled.round(4)


def _entropy_score(df: pd.DataFrame, csp_cols: list[str]) -> pd.Series:
    """
    Calcule un indice de mixité sociale basé sur l'entropie de Shannon.
    Entropie max = log(N) quand toutes les CSP sont représentées également.
    Normalisé sur 0-10.
    """
    proportions = df[csp_cols].div(df[csp_cols].sum(axis=1), axis=0)
    proportions = proportions.clip(lower=1e-10)  # éviter log(0)
    entropy = -(proportions * np.log(proportions)).sum(axis=1)
    max_entropy = np.log(len(csp_cols))
    normalized = (entropy / max_entropy * 10).round(4)
    return normalized


def process_demographics_gold() -> None:
    print("[demographics_gold] Loading Silver demographics...")
    df = pd.read_csv(DEMO_SILVER, dtype={"code_iris": str})
    df["code_iris"] = df["code_iris"].str.zfill(9)
    print("[demographics_gold]   %d zones chargées", len(df))

    csp_cols = [
        "agriculteurs", "artisans_commercants", "cadres",
        "professions_intermediaires", "employes", "ouvriers",
        "retraites", "sans_activite",
    ]

    # ── Scores individuels ───────────────────────────────────────────────
    # Revenu : plus c'est élevé, meilleur le score
    df["score_revenus"] = _robust_score(df["revenu_median"], higher_is_better=True)

    # Mixité sociale : entropie de Shannon sur les CSP
    # Zones sans données CSP → NaN
    csp_available = df[csp_cols].sum(axis=1) > 0
    df["score_mixite"] = np.nan
    df.loc[csp_available, "score_mixite"] = _entropy_score(
        df.loc[csp_available], csp_cols
    )


    # ── Score composite démographique ────────────────────────────────────
    # 50% revenus + 30% mixité + 20% seniors
    df["demographics_score"] = (
        df["score_revenus"].fillna(5) * 0.60
        + df["score_mixite"].fillna(5) * 0.40
    ).round(4)

    print("[demographics_gold] Score stats:")
    print("  revenu médian manquant : %d zones", df["revenu_median"].isna().sum())
    print("  score_revenus max/min  : %.2f / %.2f",
                df["score_revenus"].max(), df["score_revenus"].min())
    print("  score_mixite  max/min  : %.2f / %.2f",
                df["score_mixite"].max(), df["score_mixite"].min())
    print("  demographics_score avg : %.2f", df["demographics_score"].mean())

    # ── Export ───────────────────────────────────────────────────────────
    df.to_csv(DEMO_GOLD, index=False)
    print("[demographics_gold] Gold saved → %s", DEMO_GOLD.name)

    # Export MySQL
    df.to_sql("demographics", engine, if_exists="replace", index=False)
    print("[demographics_gold] MySQL 'demographics' table updated.")


if __name__ == "__main__":
    process_demographics_gold()