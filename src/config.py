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
# Indicator 2 — green spaces
ESPACES_VERTS_RAW = BRONZE / "indice_vivabilite_familiale" / "espaces_verts.geojson"
# DVF — housing transactions
DVF_RAW          = BRONZE / "public_service_data" / "ValeursFoncieres-2025.txt"
# BDCOM — public service establishments
BDCOM_RAW        = BRONZE / "public_service_data" / "BDCOM_2023.csv"
BDCOM_OD_RAW     = BRONZE / "public_service_data" / "BDCOM_2023_OD.xlsx"
# Hospitals
HOSPITALS_RAW    = BRONZE / "public_service_data" / "les_etablissements_hospitaliers_franciliens.csv"
# Indicator 3 — transport
TRANSPORT_ARRETS_RAW = BRONZE / "transport_data" / "arrets.csv"
TRANSPORT_VELIB_RAW  = BRONZE / "transport_data" / "velib.csv"


# ── Silver outputs ─────────────────────────────────────────────────────────────
IRIS_GEOJSON      = BRONZE / "main_data" / "iris.geojson"
IRIS_SILVER       = SILVER / "iris_paris.csv"
POPULATION_SILVER = SILVER / "population_paris.csv"
SCHOOLS_SILVER    = SILVER / "schools_merged.csv"

DVF_SILVER        = SILVER / "dvf_paris_clean.csv"
BDCOM_SILVER      = SILVER / "bdcom_paris_clean.csv"
HOSPITALS_SILVER  = SILVER / "hospitals_paris_clean.csv"
ESPACES_VERTS_SILVER = SILVER / "espaces_verts_paris.geojson"

# ── DVF filter settings ────────────────────────────────────────────────────────
DVF_TYPES_TO_KEEP = ["Appartement", "Maison"]
DVF_SURFACE_MIN   = 5      # m²
DVF_SURFACE_MAX   = 1000   # m²
DVF_PRIX_M2_MIN   = 1_000  # €/m²
DVF_PRIX_M2_MAX   = 50_000 # €/m²

TRANSPORT_ARRETS_SILVER = SILVER / "transport_arrets_paris.csv"
TRANSPORT_VELIB_SILVER  = SILVER / "velib_paris.csv"


# ── Gold outputs ───────────────────────────────────────────────────────────────
SCHOOL_DENSITY_GOLD      = GOLD / "schools_score_iris.csv"
# Geopandas buffer-based 0–10 score (input to vivabilité familiale)
TRANSPORT_SCORE_GOLD     = GOLD / "transport_score_iris.csv"
# Haversine density/proximity scores 0–1 (transport API /indicators/transport)
TRANSPORT_INDICATOR_GOLD = GOLD / "transport_indicator_iris.csv"
TRANSPORT_POINTS_GOLD    = GOLD / "transport_points.csv"
SERVICES_SCORE_GOLD      = GOLD / "services_score_iris.csv"
GREEN_SPACES_SCORE_GOLD  = GOLD / "green_spaces_score_iris.csv"
HEALTHCARE_SCORE_GOLD    = GOLD / "healthcare_score_iris.csv"
DAILY_SERVICES_SCORE_GOLD = GOLD / "daily_services_score_iris.csv"
FAMILY_FACTORS_GOLD      = GOLD / "family_missing_factors_iris.csv"
VIVABILITE_GOLD          = GOLD / "vivabilite_familiale_iris.csv"
# ── Pipeline settings ──────────────────────────────────────────────────────────
# Radius (metres) around each IRIS centroid used to count nearby schools/stops
BUFFER_METERS = 500

# Additional buffer for green spaces adjacency bonus
GREEN_SPACES_BUFFER_METERS = 300

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

# ── Transport weights ────────────────────────────────────────────────────────
TRANSPORT_WEIGHTS = {
    "metro": 1.0,
    "rail": 1.2,
    "tram": 0.7,
    "bus": 0.4,
    "cableway": 0.5,
    "velib": 0.3,
}

# ── Vivabilité familiale composite weights ────────────────────────────────────
# Non-price family suitability score. Childcare, safety, and environment use a
# flat neutral sub-score (5.0) until per-IRIS data is available.
VIVABILITE_WEIGHTS = {
    "school_score":         0.20,
    "childcare_score":      0.15,
    "safety_score":         0.20,
    "healthcare_score":     0.15,
    "environment_score":    0.15,
    "green_spaces_score":   0.075,
    "transport_score":      0.05,
    "daily_services_score": 0.025,
}
