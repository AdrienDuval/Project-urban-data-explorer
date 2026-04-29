"""Map-ready GeoJSON builders for frontend layers."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

import geopandas as gpd
import pandas as pd

from api.services.data_loader import DataStore


class MapDataUnavailableError(RuntimeError):
    """Raised when a requested map layer cannot be built from loaded data."""


def _clean_value(value: Any) -> Any:
    """Convert pandas/numpy scalars and missing values to JSON-safe values."""
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
    """Return a Paris arrondissement label from a 1-20 code."""
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
        features.append(
            {
                "type": "Feature",
                "geometry": feature.get("geometry"),
                "properties": properties,
            }
        )

    if not features:
        raise MapDataUnavailableError("No geometries are available for the requested layer.")

    return {"type": "FeatureCollection", "features": features}


def _score_lookup(store: DataStore) -> dict[str, dict[str, Any]]:
    scores = store.vivabilite_scores.copy()
    if scores.empty:
        raise MapDataUnavailableError(
            "Vivabilite scores are not loaded. Run `python run_pipeline.py --gold` "
            "before requesting the map layer."
        )

    if "IRIS" not in scores.columns:
        raise MapDataUnavailableError("Vivabilite scores are missing the IRIS column.")

    scores["IRIS"] = scores["IRIS"].astype(str).str.zfill(9)
    return scores.set_index("IRIS").to_dict(orient="index")


def build_vivabilite_geojson(store: DataStore) -> dict[str, Any]:
    """Return IRIS polygons joined with family liveability scores."""
    features = store.iris_geojson.get("features", [])
    if not features:
        raise MapDataUnavailableError(
            "IRIS geometry is not loaded. Run `python run_pipeline.py` "
            "before requesting the map layer."
        )

    scores_by_iris = _score_lookup(store)
    joined_features: list[dict[str, Any]] = []

    for feature in features:
        properties = feature.get("properties") or {}
        code_iris = str(properties.get("code_iris") or "").zfill(9)

        # Only Paris department (dept 75 = all arrondissements 75101–75120)
        if not code_iris.startswith("75"):
            continue

        score = scores_by_iris.get(code_iris)

        if score is None:
            # Activity / low-population zone — include as gray, no score
            map_properties: dict[str, Any] = {
                "code_iris": code_iris,
                "name": properties.get("nom_iris"),
                "arrondissement": properties.get("nom_com"),
                "quarter_code": None,
                "geography": "iris",
                "no_data": True,
                # typ_iris lets the frontend show WHY the zone has no data:
                # "A" = activity/institutional, "D" = park/water/special, "H" = residential (pipeline gap)
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

        joined_features.append(
            {
                "type": "Feature",
                "geometry": deepcopy(feature.get("geometry")),
                "properties": map_properties,
            }
        )

    if not joined_features:
        raise MapDataUnavailableError(
            "No IRIS geometries matched the loaded vivabilite scores."
        )

    return {"type": "FeatureCollection", "features": joined_features}


_PILLAR_COLS = [
    "vivabilite_score",
    "school_score",
    "healthcare_score",
    "transport_score",
    "daily_services_score",
    "green_spaces_score",
]


def build_vivabilite_arrondissement_geojson(store: DataStore) -> dict[str, Any]:
    """Return arrondissement polygons with scores aggregated from IRIS vivabilite data."""
    features = store.arrondissements_geojson.get("features", [])
    if not features:
        raise MapDataUnavailableError("Arrondissements geometry not loaded.")

    scores = store.vivabilite_scores.copy()
    if scores.empty:
        raise MapDataUnavailableError(
            "Vivabilite scores are not loaded. Run `python run_pipeline.py --gold` first."
        )

    scores["IRIS"] = scores["IRIS"].astype(str).str.zfill(9)
    # Paris IRIS codes: "75101XXXX" → digits [2:5] = "101" → arr 1, "116" → arr 16
    scores["arr_num"] = scores["IRIS"].str[2:5].astype(int) % 100

    agg_cols = [c for c in _PILLAR_COLS if c in scores.columns]
    agg_dict: dict[str, Any] = {c: "mean" for c in agg_cols}
    if "population" in scores.columns:
        agg_dict["population"] = "sum"

    agg = scores.groupby("arr_num").agg(agg_dict).reset_index()
    # Rank arrondissements by vivabilite_score descending
    if "vivabilite_score" in agg.columns:
        agg["vivabilite_rank"] = agg["vivabilite_score"].rank(
            ascending=False, method="min"
        ).astype(int)
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
        for col in list(agg_dict.keys()) + (["vivabilite_rank"] if "vivabilite_score" in agg.columns else []):
            val = agg_row.get(col)
            if val is None or (hasattr(val, "__float__") and pd.isna(val)):
                map_props[col] = None
            elif isinstance(val, float):
                map_props[col] = round(val, 2)
            else:
                map_props[col] = _clean_value(val)

        joined.append({
            "type": "Feature",
            "geometry": deepcopy(feature.get("geometry")),
            "properties": map_props,
        })

    if not joined:
        raise MapDataUnavailableError("No arrondissement features could be built.")

    return {"type": "FeatureCollection", "features": joined}


def build_thermal_comfort_geojson(store: DataStore) -> dict[str, Any]:
    """Return IRIS polygons with the thermal comfort composite and sub-metrics."""
    gdf = store.thermal_comfort_scores.copy()
    if gdf.empty:
        raise MapDataUnavailableError(
            "Thermal comfort scores are not loaded. Run `python run_pipeline.py --gold` "
            "before requesting this map layer."
        )

    gdf["thermal_score"] = (pd.to_numeric(gdf["indice_confort_thermique"], errors="coerce") / 10).round(2)
    gdf["tree_density_score"] = _normalise_0_10(gdf["densite_arbres"])
    gdf["cooling_area_score"] = _normalise_0_10(gdf["ratio_fraicheur"])
    gdf["map_id"] = gdf["code_iris"].astype(str).str.zfill(9)
    gdf["code_iris"] = gdf["map_id"]
    gdf["name"] = gdf["nom_iris"]
    gdf["arrondissement"] = gdf["code_iris"].str.slice(3, 5).map(_arrondissement_label)
    gdf["geography"] = "iris"

    keep_cols = [
        "map_id",
        "geography",
        "code_iris",
        "name",
        "arrondissement",
        "thermal_score",
        "tree_density_score",
        "cooling_area_score",
        "indice_confort_thermique",
        "densite_arbres",
        "ratio_fraicheur",
        "geometry",
    ]
    return _geojson_from_gdf(gdf[keep_cols], required_score="thermal_score")


def build_rent_geojson(store: DataStore) -> dict[str, Any]:
    """Return arrondissement polygons with median rent and affordability scores."""
    gdf = store.rent_price_scores.copy()
    if gdf.empty:
        raise MapDataUnavailableError(
            "Rent scores are not loaded. Run `python run_pipeline.py --gold` "
            "before requesting this map layer."
        )

    gdf["rent_score"] = _normalise_0_10(gdf["loyer_median_m2"], higher_is_better=False)
    gdf["map_id"] = "rent-" + gdf["c_ar"].astype(str)
    gdf["code_arrondissement"] = gdf["c_ar"].astype(str)
    gdf["name"] = gdf["l_aroff"].fillna(gdf["l_ar"])
    gdf["arrondissement"] = gdf["code_arrondissement"].map(_arrondissement_label)
    gdf["geography"] = "arrondissement"

    keep_cols = [
        "map_id",
        "geography",
        "code_arrondissement",
        "name",
        "arrondissement",
        "rent_score",
        "loyer_median_m2",
        "loyer_q1_m2",
        "loyer_q3_m2",
        "geometry",
    ]
    return _geojson_from_gdf(gdf[keep_cols], required_score="rent_score")


def build_sale_geojson(store: DataStore) -> dict[str, Any]:
    """Return latest arrondissement sale-price polygons and affordability scores."""
    gdf = store.sale_price_scores.copy()
    if gdf.empty:
        raise MapDataUnavailableError(
            "Sale price scores are not loaded. Run `python run_pipeline.py --gold` "
            "before requesting this map layer."
        )

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

    keep_cols = [
        "map_id",
        "geography",
        "code_arrondissement",
        "name",
        "arrondissement",
        "sale_score",
        "prix_m2",
        "Trimestre",
        "date_periode",
        "geometry",
    ]
    return _geojson_from_gdf(gdf[keep_cols], required_score="sale_score")
