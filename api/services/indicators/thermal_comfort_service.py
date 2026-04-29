from __future__ import annotations

import json
from typing import Optional, List

import pandas as pd
from shapely.geometry import mapping

from api.services.data_loader import DataStore


def get_thermal_comfort_map(store: DataStore) -> dict:
    """Construit le GeoJSON FeatureCollection depuis le GeoDataFrame en mémoire."""
    gdf = store.thermal_comfort_scores

    if gdf is None or gdf.empty:
        return {"type": "FeatureCollection", "features": []}

    features = []
    skipped = 0

    for _, row in gdf.iterrows():
        geom = row.get("geometry")
        if geom is None or geom.is_empty:
            skipped += 1
            continue

        try:
            geom_dict = mapping(geom)  # Shapely → dict GeoJSON
        except Exception as e:
            print(f"⚠️  Géométrie invalide pour {row.get('code_iris')}: {e}")
            skipped += 1
            continue

        def safe_float(val):
            try:
                return float(val) if pd.notna(val) else None
            except Exception:
                return None

        features.append({
            "type": "Feature",
            "geometry": geom_dict,
            "properties": {
                "code_iris": str(row.get("code_iris", "")),
                "name": str(row.get("nom_iris", "")),
                "arrondissement": str(row.get("arrondissement", "")),
                "geography": "iris",
                "population": None,
                "densite_arbres": safe_float(row.get("densite_arbres")),
                # Noms exacts attendus par le frontend
                "thermal_score": safe_float(row.get("thermal_score") or row.get("indice_confort_thermique")),
                "tree_density_score": safe_float(row.get("tree_density_score") or row.get("score_densite_arbres")),
                "cooling_area_score": safe_float(row.get("cooling_area_score") or row.get("score_ratio_fraicheur")),
            },
        })

    print(f"✅ GeoJSON : {len(features)} features, {skipped} ignorées")
    return {"type": "FeatureCollection", "features": features}


def list_thermal_comfort_indicators(
    store: DataStore,
    arrondissement: Optional[str] = None,
    min_score: Optional[float] = None,
    limit: int = 20,
    offset: int = 0,
    page: int = 1,
    size: int = 50,
) -> dict:
    df = store.thermal_comfort_scores.copy()

    if arrondissement:
        df = df[df["arrondissement"].str.contains(arrondissement, na=False)]

    score_col = "thermal_score" if "thermal_score" in df.columns else "indice_confort_thermique"

    if min_score is not None and score_col in df.columns:
        df = df[df[score_col] >= min_score]

    if score_col in df.columns:
        df = df.sort_values(score_col, ascending=False)

    # Retire la colonne geometry (non sérialisable en JSON)
    if "geometry" in df.columns:
        df = df.drop(columns=["geometry"])

    total = len(df)
    df = df.iloc[offset: offset + size]

    return {
        "items": df.where(pd.notnull(df), None).to_dict(orient="records"),
        "total": total,
        "limit": size,
        "offset": offset,
    }


def list_thermal_comfort_arrondissements(store: DataStore) -> List[dict]:
    df = store.thermal_comfort_scores.copy()

    if "geometry" in df.columns:
        df = df.drop(columns=["geometry"])

    score_col = "thermal_score" if "thermal_score" in df.columns else "indice_confort_thermique"

    if "arrondissement" not in df.columns or score_col not in df.columns:
        return []

    result = (
        df.groupby("arrondissement")
        .agg(avg_score=(score_col, "mean"), count_iris=(score_col, "count"))
        .reset_index()
    )
    return result.to_dict(orient="records")


def get_thermal_comfort_indicator(store: DataStore, code_iris: str) -> Optional[dict]:
    df = store.thermal_comfort_scores.copy()

    if "geometry" in df.columns:
        df = df.drop(columns=["geometry"])

    row = df[df["code_iris"] == code_iris]
    if row.empty:
        return None
    return row.iloc[0].where(pd.notnull(row.iloc[0]), None).to_dict()