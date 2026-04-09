"""
Central configuration: file paths and pipeline constants.
All other modules import from here — never hardcode paths elsewhere.
"""
from pathlib import Path

# Project root is one level above this file (urban-data-explorer/)
ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT_DIR / "data"

# Data lake layers
BRONZE = DATA_DIR / "bronze"
SILVER = DATA_DIR / "silver"
GOLD   = DATA_DIR / "gold"

# ── Bronze inputs ──────────────────────────────────────────────────────────────
# Main data
IRIS_RAW         = BRONZE / "main_data" / "iris.xlsx"
POPULATION_RAW   = BRONZE / "main_data" / "base-ic-evol-struct-pop-2022.CSV"
# Indicator 1 — school accessibility
COLLEGES_RAW     = BRONZE / "indice_vivabilite_familiale" / "etablissements-scolaires-colleges.xlsx"
ELEMENTAIRES_RAW = BRONZE / "indice_vivabilite_familiale" / "etablissements-scolaires-ecoles-elementaires.xlsx"
MATERNELLES_RAW  = BRONZE / "indice_vivabilite_familiale" / "etablissements-scolaires-maternelles.xlsx"
# DVF — housing transactions
DVF_RAW          = BRONZE / "public_service_data" / "ValeursFoncieres-2025.txt"
# BDCOM — public service establishments
BDCOM_RAW        = BRONZE / "public_service_data" / "BDCOM_2023.csv"
BDCOM_OD_RAW     = BRONZE / "public_service_data" / "BDCOM_2023_OD.xlsx"
# Hospitals
HOSPITALS_RAW    = BRONZE / "public_service_data" / "les_etablissements_hospitaliers_franciliens.csv"

# ── Silver outputs ─────────────────────────────────────────────────────────────
IRIS_GEOJSON      = BRONZE / "main_data" / "iris.geojson"
IRIS_SILVER       = SILVER / "iris_paris.csv"
POPULATION_SILVER = SILVER / "population_paris.csv"
SCHOOLS_SILVER    = SILVER / "schools_merged.csv"
DVF_SILVER        = SILVER / "dvf_paris_clean.csv"
BDCOM_SILVER      = SILVER / "bdcom_paris_clean.csv"
HOSPITALS_SILVER  = SILVER / "hospitals_paris_clean.csv"

# ── DVF filter settings ────────────────────────────────────────────────────────
DVF_TYPES_TO_KEEP = ["Appartement", "Maison"]
DVF_SURFACE_MIN   = 5      # m²
DVF_SURFACE_MAX   = 1000   # m²
DVF_PRIX_M2_MIN   = 1_000  # €/m²
DVF_PRIX_M2_MAX   = 50_000 # €/m²

# ── Gold outputs ───────────────────────────────────────────────────────────────
SCHOOL_DENSITY_GOLD = GOLD / "schools_score_iris.csv"

# ── Pipeline settings ──────────────────────────────────────────────────────────
# Radius (metres) around each IRIS centroid used to count nearby schools
BUFFER_METERS = 500

# IRIS zones with fewer residents than this are excluded
MIN_POPULATION = 500

# School types to include in the analysis.
# Possible values: "Collège", "Maternelle", "Elémentaire", "Polyvalent"
# Set to None to keep all types.
SCHOOL_TYPES = [
    "Collège",
    "Maternelle",
    "Elémentaire",
    "Polyvalent",
]
