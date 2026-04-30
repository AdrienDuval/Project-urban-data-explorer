"""Thread-safe TTL singleton for spatial (geometry) datasets.

Spatial GeoDataFrames (thermal comfort, rent, sale price) and GeoJSON files
are loaded here rather than at every request.  A 1-hour TTL means the data
refreshes automatically after pipeline re-runs without an API restart.
"""
from __future__ import annotations

import json
import threading
import time
from dataclasses import dataclass
from typing import Any

import geopandas as gpd
import pandas as pd
from shapely import wkt as shapely_wkt
from sqlalchemy import select

from api.db_models import thermal_comfort as thermal_tbl
from api.db_models import rent_data as rent_tbl
from api.db_models import sale_price_median as sale_tbl
from src.config import ARRONDISSEMENTS, IRIS_GEOJSON
from src.db import SessionLocal


@dataclass
class SpatialStore:
    """Spatial datasets served from memory with a process-level TTL."""

    thermal_comfort_scores: gpd.GeoDataFrame
    rent_price_scores: gpd.GeoDataFrame
    sale_price_scores: gpd.GeoDataFrame
    iris_geojson: dict[str, Any]
    arrondissements_geojson: dict[str, Any]

    @classmethod
    def load(cls) -> "SpatialStore":
        db = SessionLocal()
        try:
            thermal_gdf = _load_geodataframe(db, thermal_tbl, "code_iris", zfill=9)
            rent_gdf = _load_geodataframe(db, rent_tbl, "c_ar")
            sale_gdf = _load_geodataframe(db, sale_tbl, "c_ar")
        finally:
            db.close()

        if not rent_gdf.empty:
            rent_gdf["c_ar"] = rent_gdf["c_ar"].astype(str)
        if not sale_gdf.empty:
            sale_gdf["c_ar"] = sale_gdf["c_ar"].astype(str)

        iris_geojson = _load_geojson(IRIS_GEOJSON)
        arrondissements_geojson = _load_geojson(ARRONDISSEMENTS)

        return cls(
            thermal_comfort_scores=thermal_gdf,
            rent_price_scores=rent_gdf,
            sale_price_scores=sale_gdf,
            iris_geojson=iris_geojson,
            arrondissements_geojson=arrondissements_geojson,
        )


def _load_geodataframe(db, table, code_col: str, *, zfill: int = 0) -> gpd.GeoDataFrame:
    rows = db.execute(select(table)).mappings().all()
    if not rows:
        return gpd.GeoDataFrame()
    df = pd.DataFrame([dict(r) for r in rows])
    if "geometry" not in df.columns:
        return gpd.GeoDataFrame(df)
    df["geometry"] = df["geometry"].apply(
        lambda x: shapely_wkt.loads(x) if x else None
    )
    gdf = gpd.GeoDataFrame(df, geometry="geometry")
    if zfill and code_col in gdf.columns:
        gdf[code_col] = gdf[code_col].astype(str).str.zfill(zfill)
    return gdf


def _load_geojson(path) -> dict[str, Any]:
    if path.exists():
        with path.open(encoding="utf-8") as fh:
            return json.load(fh)
    return {"type": "FeatureCollection", "features": []}


# ---------------------------------------------------------------------------
# Thread-safe TTL singleton
# ---------------------------------------------------------------------------

_TTL = 3600.0
_lock = threading.Lock()
_store: SpatialStore | None = None
_loaded_at: float = 0.0


def get_spatial_store() -> SpatialStore:
    """Return the cached SpatialStore, reloading if the TTL has expired."""
    global _store, _loaded_at
    now = time.monotonic()
    if _store is None or (now - _loaded_at) > _TTL:
        with _lock:
            if _store is None or (now - _loaded_at) > _TTL:
                _store = SpatialStore.load()
                _loaded_at = time.monotonic()
    return _store
