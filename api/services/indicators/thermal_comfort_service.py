from __future__ import annotations

from typing import List, Optional

import pandas as pd
from shapely.geometry import mapping

from api.services.spatial_cache import SpatialStore


def get_thermal_comfort_map(spatial: SpatialStore) -> dict:
    gdf = spatial.thermal_comfort_scores
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
            geom_dict = mapping(geom)
        except Exception:
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
                "thermal_score": safe_float(row.get("thermal_score") or row.get("indice_confort_thermique")),
                "tree_density_score": safe_float(row.get("tree_density_score")),
                "cooling_area_score": safe_float(row.get("cooling_area_score")),
            },
        })

    return {"type": "FeatureCollection", "features": features}


def list_thermal_comfort_indicators(
    spatial: SpatialStore,
    arrondissement: Optional[str] = None,
    min_score: Optional[float] = None,
    offset: int = 0,
    size: int = 50,
) -> dict:
    df = spatial.thermal_comfort_scores.copy()
    if "geometry" in df.columns:
        df = df.drop(columns=["geometry"])

    if arrondissement:
        df = df[df["arrondissement"].str.contains(arrondissement, na=False)]

    score_col = "thermal_score" if "thermal_score" in df.columns else "indice_confort_thermique"
    if min_score is not None and score_col in df.columns:
        df = df[df[score_col] >= min_score]
    if score_col in df.columns:
        df = df.sort_values(score_col, ascending=False)

    total = len(df)
    df = df.iloc[offset: offset + size]
    return {
        "items": df.where(pd.notnull(df), None).to_dict(orient="records"),
        "total": total,
        "limit": size,
        "offset": offset,
    }


def list_thermal_comfort_arrondissements(spatial: SpatialStore) -> List[dict]:
    df = spatial.thermal_comfort_scores.copy()
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


def get_thermal_comfort_indicator(spatial: SpatialStore, code_iris: str) -> Optional[dict]:
    df = spatial.thermal_comfort_scores.copy()
    if "geometry" in df.columns:
        df = df.drop(columns=["geometry"])
    row = df[df["code_iris"] == code_iris]
    if row.empty:
        return None
    return row.iloc[0].where(pd.notnull(row.iloc[0]), None).to_dict()
