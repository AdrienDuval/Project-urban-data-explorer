"""Map-ready GeoJSON builders for frontend layers."""

from __future__ import annotations

import threading
from copy import deepcopy
from typing import Any

import geopandas as gpd
import pandas as pd
from cachetools import TTLCache, cached
from cachetools.keys import hashkey
from sqlalchemy import select

from api.db_models import demographics as demo_tbl
from api.db_models import vivabilite_familiale as vf
from api.services.spatial_cache import SpatialStore
from src.db import SessionLocal

_cache = TTLCache(maxsize=20, ttl=1800)
_lock = threading.Lock()


class MapDataUnavailableError(RuntimeError):
    """Raised when a requested map layer cannot be built from loaded data."""


def _clean_value(value: Any) -> Any:
    if value is None:
        return None
    try:
        if pd.isna(value):
            return None
    except (TypeError, ValueError):
        pass
    if hasattr(value, "item"):
        return value.item()
    return value


def _arrondissement_label(code: Any) -> str | None:
    if code is None:
        return None
    try:
        arrondissement = int(str(code)[-2:])
    except ValueError:
        return None
    suffix = "er" if arrondissement == 1 else "e"
    return f"Paris {arrondissement}{suffix} Arrondissement"


def _normalise_0_10(series: pd.Series, *, higher_is_better: bool = True) -> pd.Series:
    values = pd.to_numeric(series, errors="coerce")
    mn, mx = values.min(), values.max()
    if pd.isna(mn) or pd.isna(mx):
        return pd.Series([None] * len(series), index=series.index)
    if mx == mn:
        return pd.Series(5.0, index=series.index)
    scaled = (values - mn) / (mx - mn) * 10
    if not higher_is_better:
        scaled = 10 - scaled
    return scaled.round(2)


def _geojson_from_gdf(gdf: gpd.GeoDataFrame, *, required_score: str) -> dict[str, Any]:
    if gdf.empty:
        raise MapDataUnavailableError("The requested map layer has no loaded rows.")
    if required_score not in gdf.columns:
        raise MapDataUnavailableError(f"The requested map layer is missing `{required_score}`.")
    features: list[dict[str, Any]] = []
    for feature in gdf.iterfeatures(na="null"):
        properties = {
            key: _clean_value(value)
            for key, value in (feature.get("properties") or {}).items()
        }
        features.append({"type": "Feature", "geometry": feature.get("geometry"), "properties": properties})
    if not features:
        raise MapDataUnavailableError("No geometries are available for the requested layer.")
    return {"type": "FeatureCollection", "features": features}


def _load_vivabilite_scores_from_db() -> dict[str, dict[str, Any]]:
    stmt = select(vf)
    db = SessionLocal()
    try:
        rows = db.execute(stmt).mappings().all()
    finally:
        db.close()
    result: dict[str, dict[str, Any]] = {}
    for r in rows:
        d = dict(r)
        iris = str(d.get("IRIS", "")).zfill(9)
        result[iris] = d
    return result


def _load_demographics_scores_from_db() -> dict[str, dict[str, Any]]:
    stmt = select(demo_tbl)
    db = SessionLocal()
    try:
        rows = db.execute(stmt).mappings().all()
    finally:
        db.close()
    result: dict[str, dict[str, Any]] = {}
    for r in rows:
        d = dict(r)
        code = str(d.get("code_iris", "")).zfill(9)
        result[code] = d
    return result


_PILLAR_COLS = [
    "vivabilite_score", "school_score", "healthcare_score",
    "transport_score", "daily_services_score", "green_spaces_score",
]


@cached(cache=_cache, lock=_lock, key=lambda spatial: hashkey("vivabilite_iris"))
def build_vivabilite_geojson(spatial: SpatialStore) -> dict[str, Any]:
    features = spatial.iris_geojson.get("features", [])
    if not features:
        raise MapDataUnavailableError("IRIS geometry is not loaded.")

    scores_by_iris = _load_vivabilite_scores_from_db()
    joined_features: list[dict[str, Any]] = []

    for feature in features:
        properties = feature.get("properties") or {}
        code_iris = str(properties.get("code_iris") or "").zfill(9)
        if not code_iris.startswith("75"):
            continue
        score = scores_by_iris.get(code_iris)
        if score is None:
            map_properties: dict[str, Any] = {
                "code_iris": code_iris,
                "name": properties.get("nom_iris"),
                "arrondissement": properties.get("nom_com"),
                "quarter_code": None,
                "geography": "iris",
                "no_data": True,
                "typ_iris": properties.get("typ_iris"),
            }
        else:
            map_properties = {
                "code_iris": code_iris,
                "name": _clean_value(score.get("LIBIRIS")) or properties.get("nom_iris"),
                "arrondissement": _clean_value(score.get("LIBCOM")) or properties.get("nom_com"),
                "quarter_code": _clean_value(score.get("GRD_QUART")),
                "geography": "iris",
                "no_data": False,
            }
            for key, value in score.items():
                if key in {"IRIS", "code_iris", "LIBIRIS", "LIBCOM", "GRD_QUART"}:
                    continue
                map_properties[key] = _clean_value(value)

        joined_features.append({
            "type": "Feature",
            "geometry": deepcopy(feature.get("geometry")),
            "properties": map_properties,
        })

    if not joined_features:
        raise MapDataUnavailableError("No IRIS geometries matched the loaded vivabilite scores.")
    return {"type": "FeatureCollection", "features": joined_features}


@cached(cache=_cache, lock=_lock, key=lambda spatial: hashkey("vivabilite_arrondissement"))
def build_vivabilite_arrondissement_geojson(spatial: SpatialStore) -> dict[str, Any]:
    features = spatial.arrondissements_geojson.get("features", [])
    if not features:
        raise MapDataUnavailableError("Arrondissements geometry not loaded.")

    scores_by_iris = _load_vivabilite_scores_from_db()
    if not scores_by_iris:
        raise MapDataUnavailableError("Vivabilite scores are not available.")

    rows = list(scores_by_iris.values())
    scores = pd.DataFrame(rows)
    scores["IRIS"] = scores["IRIS"].astype(str).str.zfill(9)
    scores["arr_num"] = scores["IRIS"].str[2:5].astype(int) % 100

    agg_cols = [c for c in _PILLAR_COLS if c in scores.columns]
    agg_dict: dict[str, Any] = {c: "mean" for c in agg_cols}
    if "population" in scores.columns:
        agg_dict["population"] = "sum"

    agg = scores.groupby("arr_num").agg(agg_dict).reset_index()
    if "vivabilite_score" in agg.columns:
        agg["vivabilite_rank"] = agg["vivabilite_score"].rank(ascending=False, method="min").astype(int)
    agg_by_num = agg.set_index("arr_num").to_dict(orient="index")

    joined: list[dict[str, Any]] = []
    for feature in features:
        props = feature.get("properties") or {}
        c_ar = props.get("c_ar")
        if c_ar is None:
            continue
        arr_num = int(c_ar)
        suffix = "er" if arr_num == 1 else "e"
        arr_label = f"Paris {arr_num}{suffix} Arrondissement"
        agg_row = agg_by_num.get(arr_num, {})

        map_props: dict[str, Any] = {
            "code_iris": f"arr-{arr_num:02d}",
            "c_ar": arr_num,
            "name": _clean_value(props.get("l_aroff")) or _clean_value(props.get("l_ar")) or arr_label,
            "arrondissement": arr_label,
            "geography": "arrondissement",
            "no_data": not bool(agg_row),
        }
        rank_col = ["vivabilite_rank"] if "vivabilite_score" in agg.columns else []
        for col in list(agg_dict.keys()) + rank_col:
            val = agg_row.get(col)
            if val is None or (hasattr(val, "__float__") and pd.isna(val)):
                map_props[col] = None
            elif isinstance(val, float):
                map_props[col] = round(val, 2)
            else:
                map_props[col] = _clean_value(val)

        joined.append({"type": "Feature", "geometry": deepcopy(feature.get("geometry")), "properties": map_props})

    if not joined:
        raise MapDataUnavailableError("No arrondissement features could be built.")
    return {"type": "FeatureCollection", "features": joined}


@cached(cache=_cache, lock=_lock, key=lambda spatial: hashkey("thermal_comfort"))
def build_thermal_comfort_geojson(spatial: SpatialStore) -> dict[str, Any]:
    gdf = spatial.thermal_comfort_scores.copy()
    if gdf.empty:
        raise MapDataUnavailableError("Thermal comfort scores are not loaded.")

    gdf["map_id"] = gdf["code_iris"].astype(str).str.zfill(9)
    gdf["code_iris"] = gdf["map_id"]
    gdf["name"] = gdf["nom_iris"]
    gdf["arrondissement"] = gdf["code_iris"].str.slice(3, 5).map(_arrondissement_label)
    gdf["geography"] = "iris"
    gdf["thermal_score"] = pd.to_numeric(
        gdf.get("thermal_score", gdf.get("indice_confort_thermique")), errors="coerce"
    ).round(2)
    gdf["tree_density_score"] = pd.to_numeric(gdf.get("tree_density_score"), errors="coerce").round(2)
    gdf["cooling_area_score"] = pd.to_numeric(gdf.get("cooling_area_score"), errors="coerce").round(2)
    gdf["proximity_score"] = pd.to_numeric(gdf.get("proximity_score"), errors="coerce").round(2)

    keep_cols = [
        "map_id", "geography", "code_iris", "name", "arrondissement",
        "thermal_score", "tree_density_score", "cooling_area_score",
        "proximity_score", "densite_arbres", "ratio_fraicheur", "geometry",
    ]
    keep_cols = [c for c in keep_cols if c in gdf.columns]
    return _geojson_from_gdf(gdf[keep_cols], required_score="thermal_score")


@cached(cache=_cache, lock=_lock, key=lambda spatial: hashkey("rent"))
def build_rent_geojson(spatial: SpatialStore) -> dict[str, Any]:
    gdf = spatial.rent_price_scores.copy()
    if gdf.empty:
        raise MapDataUnavailableError("Rent scores are not loaded.")

    gdf["rent_score"] = _normalise_0_10(gdf["loyer_median_m2"], higher_is_better=False)
    gdf["map_id"] = "rent-" + gdf["c_ar"].astype(str)
    gdf["code_arrondissement"] = gdf["c_ar"].astype(str)
    gdf["name"] = gdf["l_aroff"].fillna(gdf["l_ar"])
    gdf["arrondissement"] = gdf["code_arrondissement"].map(_arrondissement_label)
    gdf["geography"] = "arrondissement"

    keep_cols = ["map_id", "geography", "code_arrondissement", "name", "arrondissement",
                 "rent_score", "loyer_median_m2", "loyer_q1_m2", "loyer_q3_m2", "geometry"]
    return _geojson_from_gdf(gdf[keep_cols], required_score="rent_score")


@cached(cache=_cache, lock=_lock, key=lambda spatial: hashkey("sale"))
def build_sale_geojson(spatial: SpatialStore) -> dict[str, Any]:
    gdf = spatial.sale_price_scores.copy()
    if gdf.empty:
        raise MapDataUnavailableError("Sale price scores are not loaded.")

    if "date_periode" in gdf.columns:
        gdf["date_periode"] = pd.to_datetime(gdf["date_periode"], errors="coerce")
        gdf = gdf.sort_values("date_periode").drop_duplicates("c_ar", keep="last")

    gdf["sale_score"] = _normalise_0_10(gdf["prix_m2"], higher_is_better=False)
    gdf["map_id"] = "sale-" + gdf["c_ar"].astype(str)
    gdf["code_arrondissement"] = gdf["c_ar"].astype(str)
    gdf["name"] = gdf["l_aroff"].fillna(gdf["l_ar"])
    gdf["arrondissement"] = gdf["code_arrondissement"].map(_arrondissement_label)
    gdf["geography"] = "arrondissement"
    gdf["date_periode"] = gdf["date_periode"].dt.strftime("%Y-%m-%d")

    keep_cols = ["map_id", "geography", "code_arrondissement", "name", "arrondissement",
                 "sale_score", "prix_m2", "Trimestre", "date_periode", "geometry"]
    return _geojson_from_gdf(gdf[keep_cols], required_score="sale_score")


@cached(cache=_cache, lock=_lock, key=lambda spatial: hashkey("demographics"))
def build_demographics_geojson(spatial: SpatialStore) -> dict[str, Any]:
    features_base = spatial.iris_geojson.get("features", [])
    if not features_base:
        raise MapDataUnavailableError("IRIS geometry not loaded.")

    scores_by_iris = _load_demographics_scores_from_db()
    if not scores_by_iris:
        raise MapDataUnavailableError("Demographics scores not loaded.")

    joined: list[dict[str, Any]] = []
    for feature in features_base:
        props = feature.get("properties") or {}
        code_iris = str(props.get("code_iris") or "").zfill(9)
        score = scores_by_iris.get(code_iris)
        if score is None:
            continue
        joined.append({
            "type": "Feature",
            "geometry": deepcopy(feature.get("geometry")),
            "properties": {
                "map_id": code_iris,
                "code_iris": code_iris,
                "name": _clean_value(score.get("nom_iris")) or props.get("nom_iris"),
                "arrondissement": _clean_value(score.get("arrondissement"))
                    or _arrondissement_label(code_iris[3:5]),
                "geography": "iris",
                "population": _clean_value(score.get("population")),
                "pop_0_14": _clean_value(score.get("pop_0_14")),
                "pop_15_29": _clean_value(score.get("pop_15_29")),
                "pop_65p": _clean_value(score.get("pop_65p")),
                "pct_seniors": _clean_value(score.get("pct_sans_activite")),
                "revenu_median": _clean_value(score.get("revenu_median")),
                "revenu_q1": _clean_value(score.get("revenu_q1")),
                "revenu_q3": _clean_value(score.get("revenu_q3")),
                "gini": _clean_value(score.get("gini")),
                "taux_pauvrete": _clean_value(score.get("taux_pauvrete")),
                "pct_cadres": _clean_value(score.get("pct_cadres")),
                "pct_employes": _clean_value(score.get("pct_employes")),
                "pct_ouvriers": _clean_value(score.get("pct_ouvriers")),
                "pct_retraites": _clean_value(score.get("pct_retraites")),
                "pct_sans_activite": _clean_value(score.get("pct_sans_activite")),
                "score_revenus": _clean_value(score.get("score_revenus")),
                "score_mixite": _clean_value(score.get("score_mixite")),
                "demographics_score": _clean_value(score.get("demographics_score")),
            },
        })

    if not joined:
        raise MapDataUnavailableError("No IRIS geometries matched demographics scores.")
    return {"type": "FeatureCollection", "features": joined}
