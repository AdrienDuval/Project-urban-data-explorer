"""Business logic for BDCOM commercial establishments statistics."""

from __future__ import annotations

import pandas as pd

from api.services.data_loader import DataStore


def get_bdcom_stats(store: DataStore) -> dict:
    """
    Compute summary statistics for BDCOM commercial establishments in Paris.

    Returns aggregate counts, activity breakdown, and location distribution.
    """
    df = store.bdcom_scores

    if df.empty:
        return {
            "total_establishments": 0,
            "total_surface_m2": 0,
            "avg_surface_m2": 0,
            "top_activities": [],
            "by_arrondissement": [],
        }

    stats = {
        "total_establishments": len(df),
        "total_surface_m2": float(df["surf"].sum()) if "surf" in df.columns else 0,
        "avg_surface_m2": float(df["surf"].mean()) if "surf" in df.columns else 0,
    }

    # Top activities
    if "Libellé activité (224 postes)" in df.columns:
        top_activities = (
            df["Libellé activité (224 postes)"]
            .value_counts()
            .head(10)
            .to_dict()
        )
        stats["top_activities"] = [
            {"activity": k, "count": int(v)}
            for k, v in top_activities.items()
        ]

    # Distribution by arrondissement
    if "arro" in df.columns:
        by_arro = (
            df.groupby("arro", dropna=False)
            .agg(
                count=("arro", "count"),
                surface=("surf", "sum") if "surf" in df.columns else ("arro", "count"),
            )
            .reset_index()
            .sort_values("count", ascending=False)
        )
        stats["by_arrondissement"] = [
            {"arrondissement": int(row["arro"]), "count": int(row["count"]), "total_surface": float(row["surface"])}
            for _, row in by_arro.iterrows() if pd.notna(row["arro"])
        ]

    return stats


def get_bdcom_by_type(store: DataStore) -> dict:
    """
    Get BDCOM establishments grouped by TYPE (commerce type classification).
    """
    df = store.bdcom_scores

    if df.empty or "TYPE" not in df.columns:
        return {}

    by_type = (
        df.groupby("TYPE", dropna=False)
        .agg(
            count=("TYPE", "count"),
            surface=("surf", "sum") if "surf" in df.columns else ("TYPE", "count"),
            avg_surface=("surf", "mean") if "surf" in df.columns else ("TYPE", "count"),
        )
        .reset_index()
        .sort_values("count", ascending=False)
    )

    return {
        row["TYPE"]: {
            "count": int(row["count"]),
            "total_surface": float(row["surface"]),
            "avg_surface": float(row["avg_surface"]),
        }
        for _, row in by_type.iterrows()
    }

