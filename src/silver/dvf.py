"""
Bronze → Silver: DVF housing transactions (Paris)

Loads ValeursFoncieres raw pipe-separated file, filters to Paris apartment
and house sales, parses numerics/dates, removes outliers, and saves a clean
CSV ready for Gold indicators.
"""
import pandas as pd

from src.config import (
    DVF_PRIX_M2_MAX,
    DVF_PRIX_M2_MIN,
    DVF_RAW,
    DVF_SILVER,
    DVF_SURFACE_MAX,
    DVF_SURFACE_MIN,
    DVF_TYPES_TO_KEEP,
    SILVER,
)

COLUMNS_TO_KEEP = [
    "Date mutation",
    "Nature mutation",
    "Valeur fonciere",
    "No voie",
    "Type de voie",
    "Voie",
    "Code postal",
    "Commune",
    "Code departement",
    "Code commune",
    "Section",
    "Code type local",
    "Type local",
    "Surface reelle bati",
    "Nombre pieces principales",
    "Nature culture",
]


def process_dvf() -> pd.DataFrame:
    """
    Clean and filter the DVF raw file to Paris residential sales.

    Steps:
        1. Load raw pipe-separated file, keep relevant columns
        2. Filter: Paris (dept 75) + Vente + Appartement/Maison
        3. Parse numerics (French comma decimals) and dates
        4. Derive arrondissement and prix_m2
        5. Remove outliers on surface and prix_m2
        6. Rename columns to snake_case

    Returns:
        Cleaned DataFrame saved to DVF_SILVER.
    """
    print(f"[dvf] Loading {DVF_RAW.name}...")
    df = pd.read_csv(DVF_RAW, sep="|", dtype=str, low_memory=False)
    print(f"[dvf]   → {len(df):,} rows loaded")

    # ── Select columns ────────────────────────────────────────────────────────
    available = [c for c in COLUMNS_TO_KEEP if c in df.columns]
    missing   = [c for c in COLUMNS_TO_KEEP if c not in df.columns]
    if missing:
        print(f"[dvf]   Columns not found (skipped): {missing}")
    df = df[available].copy()

    # ── Filter: Paris + Vente + property types ────────────────────────────────
    df["Code departement"] = df["Code departement"].astype(str).str.strip()
    df = df[df["Code departement"] == "75"].copy()

    df["Nature mutation"] = df["Nature mutation"].astype(str).str.strip()
    df = df[df["Nature mutation"] == "Vente"].copy()

    df["Type local"] = df["Type local"].astype(str).str.strip()
    df = df[df["Type local"].isin(DVF_TYPES_TO_KEEP)].copy()
    print(f"[dvf]   → {len(df):,} rows after Paris/Vente/type filter")

    # ── Parse numerics & dates ────────────────────────────────────────────────
    df["Valeur fonciere"] = (
        df["Valeur fonciere"]
        .astype(str)
        .str.replace(",", ".", regex=False)
        .str.replace(" ", "", regex=False)
        .pipe(pd.to_numeric, errors="coerce")
    )
    df["Surface reelle bati"] = (
        df["Surface reelle bati"]
        .astype(str)
        .str.replace(",", ".", regex=False)
        .pipe(pd.to_numeric, errors="coerce")
    )
    df["Nombre pieces principales"] = pd.to_numeric(
        df["Nombre pieces principales"], errors="coerce"
    )
    df["Date mutation"] = pd.to_datetime(df["Date mutation"], dayfirst=True, errors="coerce")
    df["annee"] = df["Date mutation"].dt.year
    df["mois"]  = df["Date mutation"].dt.month

    # ── Arrondissement & prix/m² ──────────────────────────────────────────────
    df["Code commune"] = df["Code commune"].astype(str).str.strip()
    df["arrondissement"] = pd.to_numeric(
        df["Code commune"].str[-2:], errors="coerce"
    ).astype("Int64")
    df["prix_m2"] = df["Valeur fonciere"] / df["Surface reelle bati"]

    # ── Remove outliers ───────────────────────────────────────────────────────
    before = len(df)
    df = df[df["Valeur fonciere"] > 0]
    df = df[df["Surface reelle bati"].between(DVF_SURFACE_MIN, DVF_SURFACE_MAX)]
    df = df[df["prix_m2"].between(DVF_PRIX_M2_MIN, DVF_PRIX_M2_MAX)]
    print(f"[dvf]   Removed {before - len(df):,} outliers → {len(df):,} rows remain")

    # ── Rename columns ────────────────────────────────────────────────────────
    df = df.rename(columns={
        "Date mutation"            : "date_mutation",
        "Nature mutation"          : "nature_mutation",
        "Valeur fonciere"          : "valeur_fonciere",
        "No voie"                  : "numero_voie",
        "Type de voie"             : "type_voie",
        "Voie"                     : "nom_voie",
        "Code postal"              : "code_postal",
        "Commune"                  : "commune",
        "Code departement"         : "code_departement",
        "Code commune"             : "code_commune",
        "Section"                  : "section",
        "Code type local"          : "code_type_local",
        "Type local"               : "type_local",
        "Surface reelle bati"      : "surface_m2",
        "Nombre pieces principales": "nb_pieces",
        "Nature culture"           : "nature_culture",
    })

    # ── Save ──────────────────────────────────────────────────────────────────
    SILVER.mkdir(parents=True, exist_ok=True)
    df.to_csv(DVF_SILVER, index=False, encoding="utf-8-sig")
    print(f"[dvf] {len(df):,} transactions saved → {DVF_SILVER.name}")
    print(f"      Median prix/m²: {df['prix_m2'].median():,.0f} €")
    print(f"      Types: {df['type_local'].value_counts().to_dict()}")
    return df
