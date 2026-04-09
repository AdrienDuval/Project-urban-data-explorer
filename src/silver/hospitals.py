"""
Bronze → Silver: Hospitals Île-de-France

Loads the IDF hospital establishment CSV, cleans it (dedup, types, strings,
derived fields), filters to Paris (dept 75), and saves a clean CSV.
"""
import pandas as pd

from src.config import HOSPITALS_RAW, HOSPITALS_SILVER, SILVER

MISSING_THRESHOLD = 70  # drop columns with >70% missing values

# IDF bounding box for coordinate validation
LAT_MIN, LAT_MAX = 48.1, 49.3
LNG_MIN, LNG_MAX = 1.4, 3.6


def process_hospitals() -> pd.DataFrame:
    """
    Clean and filter the IDF hospital establishments file.

    Steps:
        1. Load raw CSV
        2. Drop columns with >70% missing, then deduplicate by finess_et
        3. Fix data types: numeric coords, parse date_ouverture
        4. Clean strings (strip, collapse spaces)
        5. Derive: annee_ouverture, is_public_service, has_coordinates
        6. Filter to Paris (dept == '75')
        7. Save to silver

    Returns:
        Cleaned DataFrame saved to HOSPITALS_SILVER.
    """
    print(f"[hospitals] Loading {HOSPITALS_RAW.name}...")
    df = pd.read_csv(HOSPITALS_RAW, sep=";", low_memory=False)
    print(f"[hospitals]   → {len(df):,} rows loaded")

    # ── Drop high-missing columns ─────────────────────────────────────────────
    missing_pct = df.isnull().mean() * 100
    cols_to_drop = missing_pct[missing_pct > MISSING_THRESHOLD].index.tolist()
    essential = {"finess_et", "finess_ej", "raison_sociale", "dept", "lat", "lng"}
    cols_to_drop = [c for c in cols_to_drop if c not in essential]
    if cols_to_drop:
        print(f"[hospitals]   Dropping {len(cols_to_drop)} columns (>{MISSING_THRESHOLD}% missing)")
        df = df.drop(columns=cols_to_drop)

    # ── Deduplicate by finess_et ──────────────────────────────────────────────
    before = len(df)
    df = df.drop_duplicates()
    if "finess_et" in df.columns:
        df = df.drop_duplicates(subset=["finess_et"], keep="first")
    print(f"[hospitals]   Removed {before - len(df):,} duplicate rows")

    # ── Fix data types ────────────────────────────────────────────────────────
    for col in ["lat", "lng"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    if "date_ouverture" in df.columns:
        df["date_ouverture"] = pd.to_datetime(df["date_ouverture"], errors="coerce")

    # ── Clean strings ─────────────────────────────────────────────────────────
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].astype(str).str.strip().str.replace(r"\s+", " ", regex=True)

    if "dept" in df.columns:
        df["dept"] = df["dept"].str.upper()

    # ── Derived fields ────────────────────────────────────────────────────────
    if "date_ouverture" in df.columns:
        df["annee_ouverture"] = df["date_ouverture"].dt.year

    if "participant_service_public_hospitalier" in df.columns:
        df["is_public_service"] = (
            df["participant_service_public_hospitalier"]
            .astype(str).str.lower()
            .isin(["oui", "true", "1", "yes"])
        ).astype(int)

    if "lat" in df.columns and "lng" in df.columns:
        df["has_coordinates"] = (
            df["lat"].between(LAT_MIN, LAT_MAX) &
            df["lng"].between(LNG_MIN, LNG_MAX)
        ).astype(int)

    # ── Filter to Paris ───────────────────────────────────────────────────────
    if "dept" in df.columns:
        df = df[df["dept"].str.upper() == "PARIS"].copy()
        print(f"[hospitals]   → {len(df):,} Paris establishments kept")

    # ── Save ──────────────────────────────────────────────────────────────────
    SILVER.mkdir(parents=True, exist_ok=True)
    df.to_csv(HOSPITALS_SILVER, index=False, encoding="utf-8-sig")
    print(f"[hospitals] {len(df):,} records saved → {HOSPITALS_SILVER.name}")
    return df
