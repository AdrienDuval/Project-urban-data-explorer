"""Centralised data-loading layer.

All three silver/gold CSV files are loaded once at application startup and
stored as a ``DataStore`` dataclass that is attached to ``app.state``.
Downstream services receive the ``DataStore`` via FastAPI dependency injection
(see ``api/dependencies.py``) — they must not call ``DataStore.load()``
themselves.
"""

from __future__ import annotations

from functools import cached_property
import json
import logging

import geopandas as gpd
import pandas as pd

from src.config import (
    ARRONDISSEMENTS,
    BDCOM_GOLD,
    DEMO_GOLD,
    DVF_GOLD,
    IRIS_GEOJSON,
    POPULATION_SILVER,
    RENT_PRICE_GOLD,
    SCHOOL_DENSITY_GOLD,
    SALE_PRICE_GOLD,
    SCHOOLS_SILVER,
    THERMAL_COMFORT_GOLD,
    TRANSPORT_INDICATOR_GOLD,
    TRANSPORT_POINTS_GOLD,
    VIVABILITE_GOLD,
)

logger = logging.getLogger(__name__)


def _clean_df(df: pd.DataFrame) -> pd.DataFrame:
    """Replace NaN / NaT with None so Pydantic can serialise the rows."""
    return df.where(pd.notnull(df), other=None)


def _read_geo_gold(path) -> gpd.GeoDataFrame:
    """Read a geo gold file, tolerating Parquet *or* CSV-with-WKT content.

    Some gold scripts write ``to_csv`` to a ``.parquet`` path, so read_parquet
    fails on those files. Fall back to reading as CSV and parsing the WKT
    ``geometry`` column into a real GeoDataFrame.
    """
    try:
        return gpd.read_parquet(path)
    except Exception:
        df = pd.read_csv(path)
        if "geometry" in df.columns:
            geometry = gpd.GeoSeries.from_wkt(df["geometry"].astype(str))
            return gpd.GeoDataFrame(df.drop(columns=["geometry"]), geometry=geometry, crs="EPSG:4326")
        return gpd.GeoDataFrame(df)


class DataStore:
    """Lazily-loaded snapshot of all datasets used by the API.

    Each dataset is read from disk on **first access** and cached for the
    process lifetime via ``functools.cached_property``. Nothing is read at
    startup, so the API starts instantly and a missing or corrupt file only
    affects the endpoints that actually touch it.

    The service-facing interface is unchanged: callers still read
    ``store.iris_scores``, ``store.sale_price_scores`` etc. as attributes.
    """

    @classmethod
    def load(cls) -> "DataStore":
        """Return a store whose datasets load lazily on first access."""
        return cls()

    # -- geometry -------------------------------------------------------
    @cached_property
    def iris_geojson(self) -> dict:
        if not IRIS_GEOJSON.exists():
            logger.warning("IRIS GeoJSON not found: %s — run `python run_pipeline.py`", IRIS_GEOJSON)
            return {"type": "FeatureCollection", "features": []}
        logger.info("Loading geometry: %s", IRIS_GEOJSON.name)
        with IRIS_GEOJSON.open(encoding="utf-8") as fh:
            return json.load(fh)

    @cached_property
    def arrondissements_geojson(self) -> dict:
        if not ARRONDISSEMENTS.exists():
            logger.warning("Arrondissements GeoJSON not found: %s", ARRONDISSEMENTS)
            return {"type": "FeatureCollection", "features": []}
        logger.info("Loading geometry: %s", ARRONDISSEMENTS.name)
        with ARRONDISSEMENTS.open(encoding="utf-8") as fh:
            return json.load(fh)

    # -- silver / gold tables ------------------------------------------
    @cached_property
    def iris_scores(self) -> pd.DataFrame:
        if not SCHOOL_DENSITY_GOLD.exists():
            logger.warning("Gold file not found: %s — run `python run_pipeline.py`", SCHOOL_DENSITY_GOLD)
            return pd.DataFrame()
        logger.info("Loading gold: %s", SCHOOL_DENSITY_GOLD.name)
        df = pd.read_csv(SCHOOL_DENSITY_GOLD, dtype={"code_iris": str})
        df["code_iris"] = df["code_iris"].str.zfill(9)
        df["school_count"] = df["school_count"].fillna(0).astype(int)
        return _clean_df(df)

    @cached_property
    def schools(self) -> pd.DataFrame:
        if not SCHOOLS_SILVER.exists():
            logger.warning("Silver file not found: %s — run `python run_pipeline.py`", SCHOOLS_SILVER)
            return pd.DataFrame()
        logger.info("Loading silver: %s", SCHOOLS_SILVER.name)
        return _clean_df(pd.read_csv(SCHOOLS_SILVER, dtype={"code_insee": str}))

    @cached_property
    def population(self) -> pd.DataFrame:
        if not POPULATION_SILVER.exists():
            logger.warning("Silver file not found: %s — run `python run_pipeline.py`", POPULATION_SILVER)
            return pd.DataFrame()
        logger.info("Loading silver: %s", POPULATION_SILVER.name)
        df = pd.read_csv(POPULATION_SILVER, dtype={"IRIS": str})
        df["IRIS"] = df["IRIS"].str.zfill(9)
        return _clean_df(df)

    @cached_property
    def transport_scores(self) -> pd.DataFrame:
        if not TRANSPORT_INDICATOR_GOLD.exists():
            return pd.DataFrame()
        df = pd.read_csv(TRANSPORT_INDICATOR_GOLD, dtype={"CODE_IRIS": str})
        df["CODE_IRIS"] = df["CODE_IRIS"].str.zfill(9)
        return _clean_df(df)

    @cached_property
    def transport_points(self) -> pd.DataFrame:
        if not TRANSPORT_POINTS_GOLD.exists():
            return pd.DataFrame()
        return _clean_df(pd.read_csv(TRANSPORT_POINTS_GOLD, dtype={"id": str}))

    @cached_property
    def vivabilite_scores(self) -> pd.DataFrame:
        if not VIVABILITE_GOLD.exists():
            logger.warning("Gold file not found: %s — run `python run_pipeline.py`", VIVABILITE_GOLD)
            return pd.DataFrame()
        logger.info("Loading gold: %s", VIVABILITE_GOLD.name)
        df = pd.read_csv(VIVABILITE_GOLD, dtype={"IRIS": str, "code_iris": str})
        df["IRIS"] = df["IRIS"].str.zfill(9)
        return _clean_df(df)

    @cached_property
    def thermal_comfort_scores(self) -> gpd.GeoDataFrame:
        if not THERMAL_COMFORT_GOLD.exists():
            logger.warning("Gold file not found: %s — run `python run_pipeline.py --gold`", THERMAL_COMFORT_GOLD)
            return gpd.GeoDataFrame()
        logger.info("Loading gold: %s", THERMAL_COMFORT_GOLD.name)
        gdf = _read_geo_gold(THERMAL_COMFORT_GOLD)
        if "code_iris" in gdf.columns:
            gdf["code_iris"] = gdf["code_iris"].astype(str).str.zfill(9)
        return gdf

    @cached_property
    def rent_price_scores(self) -> gpd.GeoDataFrame:
        if not RENT_PRICE_GOLD.exists():
            logger.warning("Gold file not found: %s — run `python run_pipeline.py --gold`", RENT_PRICE_GOLD)
            return gpd.GeoDataFrame()
        logger.info("Loading gold: %s", RENT_PRICE_GOLD.name)
        gdf = _read_geo_gold(RENT_PRICE_GOLD)
        gdf["c_ar"] = gdf["c_ar"].astype(str)
        return gdf

    @cached_property
    def sale_price_scores(self) -> gpd.GeoDataFrame:
        if not SALE_PRICE_GOLD.exists():
            logger.warning("Gold file not found: %s — run `python run_pipeline.py --gold`", SALE_PRICE_GOLD)
            return gpd.GeoDataFrame()
        logger.info("Loading gold: %s", SALE_PRICE_GOLD.name)
        gdf = _read_geo_gold(SALE_PRICE_GOLD)
        gdf["c_ar"] = gdf["c_ar"].astype(str)
        return gdf

    @cached_property
    def bdcom_scores(self) -> pd.DataFrame:
        if not BDCOM_GOLD.exists():
            logger.warning("Gold file not found: %s — run `python run_pipeline.py`", BDCOM_GOLD)
            return pd.DataFrame()
        logger.info("Loading gold: %s", BDCOM_GOLD.name)
        df = pd.read_csv(BDCOM_GOLD, dtype={"code_iris": str})
        df["code_iris"] = df["code_iris"].str.zfill(9)
        return _clean_df(df)

    @cached_property
    def dvf_scores(self) -> pd.DataFrame:
        if not DVF_GOLD.exists():
            logger.warning("Gold file not found: %s — run `python run_pipeline.py`", DVF_GOLD)
            return pd.DataFrame()
        logger.info("Loading gold: %s", DVF_GOLD.name)
        df = pd.read_csv(DVF_GOLD)
        if "code_iris" in df.columns:
            df["code_iris"] = df["code_iris"].astype(str).str.zfill(9)
        return _clean_df(df)

    @cached_property
    def demographics_scores(self) -> pd.DataFrame:
        if not DEMO_GOLD.exists():
            logger.warning("Gold file not found: %s", DEMO_GOLD)
            return pd.DataFrame()
        logger.info("Loading gold: %s", DEMO_GOLD.name)
        df = pd.read_csv(DEMO_GOLD, dtype={"code_iris": str})
        df["code_iris"] = df["code_iris"].str.zfill(9)
        return _clean_df(df)

