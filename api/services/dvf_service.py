"""Business logic for DVF housing transactions statistics."""

from __future__ import annotations

import pandas as pd

from api.services.data_loader import DataStore


def get_dvf_stats(store: DataStore) -> dict:
    """
    Compute summary statistics for DVF housing transactions in Paris.

    Returns transaction counts, price statistics, and location breakdown.
    """
    df = store.dvf_scores

    if df.empty:
        return {
            "total_transactions": 0,
            "median_prix_m2": 0,
            "median_surface_m2": 0,
            "total_value": 0,
            "price_range": {"min": 0, "max": 0},
            "by_arrondissement": [],
            "by_type": [],
        }

    stats = {
        "total_transactions": len(df),
        "median_prix_m2": float(df["prix_m2"].median()) if "prix_m2" in df.columns else 0,
        "median_surface_m2": float(df["surface_m2"].median()) if "surface_m2" in df.columns else 0,
        "total_value": float(df["valeur_fonciere"].sum()) if "valeur_fonciere" in df.columns else 0,
    }

    # Price range
    if "prix_m2" in df.columns:
        stats["price_range"] = {
            "min": float(df["prix_m2"].min()),
            "max": float(df["prix_m2"].max()),
        }

    # Distribution by arrondissement
    if "arrondissement" in df.columns:
        by_arro = (
            df.groupby("arrondissement", dropna=False)
            .agg(
                count=("arrondissement", "count"),
                avg_prix_m2=("prix_m2", "mean") if "prix_m2" in df.columns else ("arrondissement", "count"),
                total_value=("valeur_fonciere", "sum") if "valeur_fonciere" in df.columns else ("arrondissement", "count"),
            )
            .reset_index()
            .sort_values("count", ascending=False)
        )
        stats["by_arrondissement"] = [
            {
                "arrondissement": int(row["arrondissement"]) if pd.notna(row["arrondissement"]) else 0,
                "count": int(row["count"]),
                "avg_prix_m2": float(row["avg_prix_m2"]),
                "total_value": float(row["total_value"]),
            }
            for _, row in by_arro.iterrows()
        ]

    # Distribution by property type
    if "type_local" in df.columns:
        by_type = (
            df.groupby("type_local", dropna=False)
            .agg(
                count=("type_local", "count"),
                avg_prix_m2=("prix_m2", "mean") if "prix_m2" in df.columns else ("type_local", "count"),
                avg_surface=("surface_m2", "mean") if "surface_m2" in df.columns else ("type_local", "count"),
            )
            .reset_index()
            .sort_values("count", ascending=False)
        )
        stats["by_type"] = [
            {
                "type": str(row["type_local"]),
                "count": int(row["count"]),
                "avg_prix_m2": float(row["avg_prix_m2"]),
                "avg_surface": float(row["avg_surface"]),
            }
            for _, row in by_type.iterrows()
        ]

    return stats


def get_dvf_years(store: DataStore) -> dict:
    """Return available years and the min/max range for UI year-filter controls."""
    df = store.dvf_scores
    if df.empty or "annee" not in df.columns:
        return {"years": [], "min": None, "max": None}

    years = sorted(df["annee"].dropna().astype(int).unique().tolist())
    return {
        "years": years,
        "min": years[0] if years else None,
        "max": years[-1] if years else None,
    }


def get_dvf_by_iris(store: DataStore, code_iris: str) -> dict:
    """
    Return DVF housing transaction statistics for a single IRIS zone.
    """
    df = store.dvf_scores

    if df.empty or "code_iris" not in df.columns:
        return {"code_iris": code_iris, "total_transactions": 0, "median_prix_m2": 0, "median_surface_m2": 0}

    zone = df[df["code_iris"] == code_iris.zfill(9)]

    if zone.empty:
        return {"code_iris": code_iris, "total_transactions": 0, "median_prix_m2": 0, "median_surface_m2": 0}

    result: dict = {
        "code_iris": code_iris,
        "total_transactions": len(zone),
        "median_prix_m2": float(zone["prix_m2"].median()) if "prix_m2" in zone.columns else 0,
        "median_surface_m2": float(zone["surface_m2"].median()) if "surface_m2" in zone.columns else 0,
        "total_value": float(zone["valeur_fonciere"].sum()) if "valeur_fonciere" in zone.columns else 0,
    }

    if "prix_m2" in zone.columns:
        result["price_range"] = {
            "min": float(zone["prix_m2"].min()),
            "max": float(zone["prix_m2"].max()),
        }

    if "annee" in zone.columns:
        result["by_year"] = {
            int(yr): int(cnt)
            for yr, cnt in zone["annee"].value_counts().sort_index().items()
            if pd.notna(yr)
        }

    if "type_local" in zone.columns:
        result["by_type"] = {
            str(t): int(c)
            for t, c in zone["type_local"].value_counts().items()
            if pd.notna(t)
        }

    return result


def get_dvf_by_year(store: DataStore) -> dict:
    """
    Get DVF transactions grouped by year for trend analysis.
    """
    df = store.dvf_scores

    if df.empty or "annee" not in df.columns:
        return {}

    by_year = (
        df.groupby("annee", dropna=False)
        .agg(
            count=("annee", "count"),
            avg_prix_m2=("prix_m2", "mean") if "prix_m2" in df.columns else ("annee", "count"),
            total_value=("valeur_fonciere", "sum") if "valeur_fonciere" in df.columns else ("annee", "count"),
        )
        .reset_index()
        .sort_values("annee")
    )

    return {
        int(row["annee"]): {
            "count": int(row["count"]),
            "avg_prix_m2": float(row["avg_prix_m2"]),
            "total_value": float(row["total_value"]),
        }
        for _, row in by_year.iterrows() if pd.notna(row["annee"])
    }

