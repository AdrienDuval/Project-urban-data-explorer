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
#Main data
IRIS_RAW         = BRONZE / "main_data" / "iris.xlsx"
POPULATION_RAW   = BRONZE / "main_data" / "base-ic-evol-struct-pop-2019.xlsx"
#Indicator 1
COLLEGES_RAW     = BRONZE / "indice_vivabilite_familiale" / "etablissements-scolaires-colleges.xlsx"
ELEMENTAIRES_RAW = BRONZE / "indice_vivabilite_familiale" / "etablissements-scolaires-ecoles-elementaires.xlsx"
MATERNELLES_RAW  = BRONZE / "indice_vivabilite_familiale" / "etablissements-scolaires-maternelles.xlsx"

# ── Silver outputs ─────────────────────────────────────────────────────────────
IRIS_GEOJSON      = SILVER / "iris.geojson"        # pre-existing full IDF GeoJSON
IRIS_SILVER       = SILVER / "iris_paris.xlsx"
POPULATION_SILVER = SILVER / "population_paris.csv"
SCHOOLS_SILVER    = SILVER / "schools_merged.csv"

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
