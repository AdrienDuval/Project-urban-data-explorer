"""
Gold family-support sub-scores for the vivabilité familiale indicator.

This module adds the non-price factors that can be computed from currently
available data:

- healthcare_score: hospitals + pharmacy/medical BDCOM establishments
- daily_services_score: everyday services excluding healthcare

It also writes neutral 5.0 sub-scores for childcare, safety, and environment
(flat baseline until dedicated datasets are wired in; no per-zone variation).
"""

from __future__ import annotations

from typing import Callable

import geopandas as gpd
import pandas as pd

from src.config import (
    BDCOM_SILVER,
    BUFFER_METERS,
    DAILY_SERVICES_SCORE_GOLD,
    FAMILY_FACTORS_GOLD,
    HEALTHCARE_SCORE_GOLD,
    HOSPITALS_SILVER,
    IRIS_GEOJSON,
    IRIS_SILVER,
    POPULATION_SILVER,
)
from src.db import engine


HEALTHCARE_BDCOM_WEIGHT = 1.5
HOSPITAL_WEIGHT = 3.0
DAILY_SERVICE_WEIGHT = 1.0
NEUTRAL_PLACEHOLDER_SCORE = 5.0


def _normalize_0_10(series: pd.Series) -> pd.Series:
    mn, mx = series.min(), series.max()
    if mx == mn:
        return pd.Series(5.0, index=series.index)
    return ((series - mn) / (mx - mn) * 10).round(2)


def _label_column(df: pd.DataFrame, level: str) -> str:
    """Return a BDCOM label column despite source encoding drift."""
    for col in df.columns:
        if "Libell" in col and level in col:
            return col
    raise KeyError(f"BDCOM label column for level {level} not found")


def _base_iris() -> pd.DataFrame:
    population = pd.read_csv(POPULATION_SILVER, dtype={"IRIS": str})
    population["IRIS"] = population["IRIS"].str.zfill(9)

    iris_meta = pd.read_csv(IRIS_SILVER, dtype={"CODE_IRIS": str})
    iris_meta = iris_meta[["CODE_IRIS", "NOM_COM", "NOM_IRIS", "IRIS"]].rename(
        columns={
            "CODE_IRIS": "code_iris",
            "NOM_COM": "LIBCOM",
            "NOM_IRIS": "LIBIRIS",
            "IRIS": "GRD_QUART",
        }
    )
    iris_meta["code_iris"] = iris_meta["code_iris"].str.zfill(9)

    base = population.copy()
    base["code_iris"] = base["IRIS"]
    return base.merge(iris_meta, on="code_iris", how="left")


def _iris_buffer() -> gpd.GeoDataFrame:
    iris = gpd.read_file(IRIS_GEOJSON)
    iris = iris[iris["dep"] == "75"].copy()
    iris_proj = iris[["code_iris", "geometry"]].to_crs(epsg=2154).copy()
    iris_proj["IRIS"] = iris_proj["code_iris"].astype(str).str.zfill(9)
    iris_proj["geometry"] = iris_proj.geometry.buffer(BUFFER_METERS)
    return iris_proj[["IRIS", "geometry"]]


def _bdcom_points(predicate: Callable[[pd.DataFrame], pd.Series]) -> gpd.GeoDataFrame:
    bdcom = pd.read_csv(BDCOM_SILVER, encoding="utf-8-sig")
    bdcom = bdcom[predicate(bdcom)].copy()
    bdcom = bdcom[["X", "Y"]].dropna()
    return gpd.GeoDataFrame(
        bdcom,
        geometry=gpd.points_from_xy(bdcom["X"], bdcom["Y"]),
        crs="EPSG:2154",
    )


def _aggregate_points(points: gpd.GeoDataFrame, count_col: str, weight: float) -> pd.DataFrame:
    if points.empty:
        return pd.DataFrame(columns=["IRIS", count_col, f"weighted_{count_col}"])

    points = points.copy()
    points["weight"] = weight
    joined = gpd.sjoin(points, _iris_buffer(), how="inner", predicate="within")
    return (
        joined.groupby("IRIS")
        .agg(**{count_col: ("weight", "count"), f"weighted_{count_col}": ("weight", "sum")})
        .reset_index()
    )


def compute_healthcare_score() -> pd.DataFrame:
    """Compute healthcare access from hospitals and pharmacy/medical services."""
    print("[healthcare_score] Loading hospital and BDCOM health data...")

    hospitals = pd.read_csv(HOSPITALS_SILVER, encoding="utf-8-sig")
    hospitals = hospitals[hospitals["has_coordinates"] == 1].copy()
    hospitals = hospitals[["lat", "lng"]].dropna()
    hospital_geo = gpd.GeoDataFrame(
        hospitals,
        geometry=gpd.points_from_xy(hospitals["lng"], hospitals["lat"]),
        crs="EPSG:4326",
    ).to_crs(epsg=2154)

    def is_healthcare(df: pd.DataFrame) -> pd.Series:
        label_47 = df[_label_column(df, "47 postes")].astype(str).str.lower()
        label_18 = df[_label_column(df, "18 postes")].astype(str).str.lower()
        return label_47.str.contains("pharmacie|m.dic|opticien", regex=True) | label_18.str.contains(
            "sant", regex=True
        )

    bdcom_health = _bdcom_points(is_healthcare)

    hospital_agg = _aggregate_points(hospital_geo, "hospital_count", HOSPITAL_WEIGHT)
    health_agg = _aggregate_points(
        bdcom_health, "healthcare_service_count", HEALTHCARE_BDCOM_WEIGHT
    )

    result = _base_iris()
    result = result.merge(hospital_agg, on="IRIS", how="left")
    result = result.merge(health_agg, on="IRIS", how="left")

    for col in [
        "hospital_count",
        "weighted_hospital_count",
        "healthcare_service_count",
        "weighted_healthcare_service_count",
    ]:
        result[col] = result[col].fillna(0)

    result["hospital_count"] = result["hospital_count"].astype(int)
    result["healthcare_service_count"] = result["healthcare_service_count"].astype(int)
    result["weighted_healthcare_access"] = (
        result["weighted_hospital_count"] + result["weighted_healthcare_service_count"]
    )
    result["healthcare_score"] = _normalize_0_10(result["weighted_healthcare_access"])

    HEALTHCARE_SCORE_GOLD.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(HEALTHCARE_SCORE_GOLD, index=False)
    result.to_sql("healthcare_score", engine, if_exists="replace", index=False)
    print(f"[healthcare_score] {len(result)} IRIS zones saved → {HEALTHCARE_SCORE_GOLD.name} + DB")
    return result


def compute_daily_services_score() -> pd.DataFrame:
    """Compute everyday services excluding health-specific establishments."""
    print("[daily_services_score] Loading BDCOM daily service data...")

    def is_daily_service(df: pd.DataFrame) -> pd.Series:
        label_47 = df[_label_column(df, "47 postes")].astype(str).str.lower()
        label_18 = df[_label_column(df, "18 postes")].astype(str).str.lower()
        health = label_47.str.contains("pharmacie|m.dic|opticien", regex=True) | label_18.str.contains(
            "sant", regex=True
        )
        food_or_services = df["niv8"].isin({2, 4})
        family_amenities = label_47.str.contains(
            "poste|t.l.communications|banques|librairie|culturels|loisirs|sport",
            regex=True,
        )
        return (food_or_services | family_amenities) & ~health

    daily_services = _bdcom_points(is_daily_service)
    daily_agg = _aggregate_points(daily_services, "daily_service_count", DAILY_SERVICE_WEIGHT)

    result = _base_iris().merge(daily_agg, on="IRIS", how="left")
    result["daily_service_count"] = result["daily_service_count"].fillna(0).astype(int)
    result["weighted_daily_service_count"] = result["weighted_daily_service_count"].fillna(0.0)
    result["daily_services_score"] = _normalize_0_10(result["weighted_daily_service_count"])

    DAILY_SERVICES_SCORE_GOLD.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(DAILY_SERVICES_SCORE_GOLD, index=False)
    result.to_sql("daily_services_score", engine, if_exists="replace", index=False)
    print(
        f"[daily_services_score] {len(result)} IRIS zones saved → "
        f"{DAILY_SERVICES_SCORE_GOLD.name} + DB"
    )
    return result


def compute_neutral_family_factors() -> pd.DataFrame:
    """Flat 5.0 sub-scores for factors not yet driven by per-IRIS data."""
    result = _base_iris()
    for factor in ("childcare", "safety", "environment"):
        result[f"{factor}_score"] = NEUTRAL_PLACEHOLDER_SCORE

    FAMILY_FACTORS_GOLD.parent.mkdir(parents=True, exist_ok=True)
    result.to_csv(FAMILY_FACTORS_GOLD, index=False)
    result.to_sql("family_missing_factors", engine, if_exists="replace", index=False)
    print(f"[family_factors] {len(result)} neutral factor rows saved → {FAMILY_FACTORS_GOLD.name} + DB")
    return result


def compute_family_support_scores() -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    healthcare = compute_healthcare_score()
    daily_services = compute_daily_services_score()
    neutral_factors = compute_neutral_family_factors()
    return healthcare, daily_services, neutral_factors
