"""
Bronze → Silver: BDCOM public services (Paris)

Merges BDCOM_2023.csv (establishment records) with BDCOM_2023_OD.xlsx
(activity label dictionary) on the activity code, cleans the result,
and saves a consolidated CSV for Gold indicators.
"""
import pandas as pd

from src.config import BDCOM_OD_RAW, BDCOM_RAW, BDCOM_SILVER, SILVER

MISSING_THRESHOLD = 50  # drop columns with >50% missing values

# Columns that should be integers
INT_COLS = [
    "OBJECTID", "c_ord", "arro", "qua", "num", "seq", "bio", "surf",
    "cc_id", "cc_niv", "niv47", "niv18", "niv8", "niv2",
    "Code activité 47 postes", "Code activité 18 postes",
    "Code activité 8 postes", "Code activité 2 postes",
]

# Columns that should be floats (coordinates)
FLOAT_COLS = ["X", "Y", "xbis", "ybis"]

# Categorical activity label columns to fill with 'Unknown'
CATEGORICAL_ACTIVITY_COLS = [
    "Libellé activité (224 postes)", "TYPE", "Libellé TYPE (local)",
    "Libellé activité 47 postes", "Libellé activité 18 postes",
    "Libellé activité 8 postes)", "Libellé activité 2 postes",
]


def process_bdcom() -> pd.DataFrame:
    """
    Merge, clean, and filter BDCOM public-service establishment data.

    Steps:
        1. Load BDCOM CSV and OD Excel, merge on activity code
        2. Drop merge indicator, duplicates, and high-missing columns
        3. Fill remaining missing values
        4. Fix data types and clean strings
        5. Save to silver

    Returns:
        Cleaned DataFrame saved to BDCOM_SILVER.
    """
    print(f"[bdcom] Loading {BDCOM_RAW.name}...")
    df_bdcom = pd.read_csv(BDCOM_RAW)
    print(f"[bdcom]   → {len(df_bdcom):,} rows")

    print(f"[bdcom] Loading {BDCOM_OD_RAW.name}...")
    df_od = pd.read_excel(BDCOM_OD_RAW)
    df_od = df_od.rename(columns={"Code activité (224 postes)": "codact"})

    # ── Merge ─────────────────────────────────────────────────────────────────
    df = pd.merge(df_bdcom, df_od, on="codact", how="left", indicator=True)
    print(f"[bdcom]   → {len(df):,} rows after merge")
    df = df.drop(columns=["_merge"])

    # ── Drop duplicates ───────────────────────────────────────────────────────
    before = len(df)
    df = df.drop_duplicates()
    print(f"[bdcom]   Removed {before - len(df):,} duplicate rows")

    # ── Drop high-missing columns ─────────────────────────────────────────────
    missing_pct = df.isnull().mean() * 100
    cols_to_drop = missing_pct[missing_pct > MISSING_THRESHOLD].index.tolist()
    if cols_to_drop:
        print(f"[bdcom]   Dropping {len(cols_to_drop)} columns (>{MISSING_THRESHOLD}% missing)")
        df = df.drop(columns=cols_to_drop)

    # ── Fill missing values ───────────────────────────────────────────────────
    if "let" in df.columns:
        df["let"] = df["let"].fillna("")

    for col in ["cc_id", "cc_niv"]:
        if col in df.columns:
            df[col] = df[col].fillna(0)

    for col in CATEGORICAL_ACTIVITY_COLS:
        if col in df.columns and df[col].isnull().any():
            df[col] = df[col].fillna("Unknown")

    # ── Fix data types ────────────────────────────────────────────────────────
    for col in INT_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0).astype(int)

    for col in FLOAT_COLS:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")

    # ── Clean strings ─────────────────────────────────────────────────────────
    for col in df.select_dtypes(include="object").columns:
        df[col] = df[col].astype(str).str.strip().str.replace(r"\s+", " ", regex=True)

    # ── Save ──────────────────────────────────────────────────────────────────
    SILVER.mkdir(parents=True, exist_ok=True)
    df.to_csv(BDCOM_SILVER, index=False, encoding="utf-8-sig")
    print(f"[bdcom] {len(df):,} records saved → {BDCOM_SILVER.name}")
    return df
