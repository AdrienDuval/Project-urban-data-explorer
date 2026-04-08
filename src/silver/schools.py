"""
Bronze → Silver: Schools

Merges the three school datasets (colleges, elementaires, maternelles),
deduplicates, filters by school type, and extracts lat/lng coordinates.

School types available in the source data:
    "Collège"       — secondary schools (age 11-15)
    "Maternelle"    — nursery schools (age 3-6)
    "Elémentaire"   — primary schools (age 6-11)
    "Polyvalent"    — multi-level schools (cover several age groups)

To filter the types included in the output, edit SCHOOL_TYPES in config.py.
"""
from typing import List, Optional

import pandas as pd

from src.config import (
    COLLEGES_RAW,
    ELEMENTAIRES_RAW,
    MATERNELLES_RAW,
    SCHOOL_TYPES,
    SCHOOLS_SILVER,
)

# Mapping from raw column names (which differ across the 3 files) to a
# single shared schema.
_RENAME_MAP = {
    "Libellé établissement": "name",
    "Adresse": "address",
    "Arrondissement": "arrondissement",
    "Code INSEE": "code_insee",
    "Année scolaire": "annee_scolaire",
    "Type établissement": "type",
    "geo_point_2d": "geo_point",
}

_COLS = ["name", "address", "arrondissement", "code_insee", "annee_scolaire", "type", "geo_point"]


def _load(path) -> pd.DataFrame:
    """Load one school Excel file and normalise its column names."""
    df = pd.read_excel(path)
    df = df.rename(columns=_RENAME_MAP)
    return df[_COLS]


def process_schools(school_types: Optional[List[str]] = SCHOOL_TYPES) -> pd.DataFrame:
    """
    Merge, deduplicate, and clean all school data.

    Args:
        school_types: which school types to keep.
                      Defaults to SCHOOL_TYPES from config.py.
                      Pass None to keep every type.

    Returns:
        DataFrame with columns:
            name, address, arrondissement, code_insee,
            annee_scolaire, type, lat, lng
    """
    colleges     = _load(COLLEGES_RAW)
    elementaires = _load(ELEMENTAIRES_RAW)
    maternelles  = _load(MATERNELLES_RAW)

    schools = pd.concat([colleges, elementaires, maternelles], ignore_index=True)

    # ── Filter by school type ────────────────────────────────────────────────
    if school_types is not None:
        before = len(schools)
        schools = schools[schools["type"].isin(school_types)]
        print(f"[schools] type filter kept {len(schools)}/{before} rows "
              f"({', '.join(school_types)})")

    # ── Deduplicate: keep most recent year per school ────────────────────────
    schools = schools.sort_values("annee_scolaire", ascending=False)
    schools = schools.drop_duplicates(subset=["name", "address"], keep="first")

    # ── Extract coordinates from "lat, lng" string ───────────────────────────
    schools[["lat", "lng"]] = schools["geo_point"].str.split(",", n=1, expand=True)
    schools["lat"] = pd.to_numeric(schools["lat"], errors="coerce")
    schools["lng"] = pd.to_numeric(schools["lng"], errors="coerce")
    schools = schools.drop(columns=["geo_point"])
    schools = schools.dropna(subset=["lat", "lng"])

    schools.to_csv(SCHOOLS_SILVER, index=False)
    print(f"[schools] {len(schools)} schools saved → {SCHOOLS_SILVER.name}")
    print(f"  Breakdown: {schools['type'].value_counts().to_dict()}")
    return schools
