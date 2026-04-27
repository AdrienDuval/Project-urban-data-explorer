"""Map-ready GeoJSON builders for frontend layers."""

from __future__ import annotations

from copy import deepcopy
from typing import Any

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
        score = scores_by_iris.get(code_iris)
        if score is None:
            continue

        map_properties = {
            "code_iris": code_iris,
            "name": _clean_value(score.get("LIBIRIS")) or properties.get("nom_iris"),
            "arrondissement": _clean_value(score.get("LIBCOM")) or properties.get("nom_com"),
            "quarter_code": _clean_value(score.get("GRD_QUART")),
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
