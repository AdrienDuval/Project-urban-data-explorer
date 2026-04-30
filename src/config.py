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
IRIS_RAW                = BRONZE / "main_data" / "iris.xlsx"
IRIS_GEOJSON            = BRONZE / "main_data" / "iris.geojson"
POPULATION_RAW          = BRONZE / "main_data" / "base-ic-evol-struct-pop-2022.CSV"
ARRONDISSEMENTS         = BRONZE / "main_data" / "arrondissements.geojson"
# Indicator 1 — school accessibility
COLLEGES_RAW     = BRONZE / "indice_vivabilite_familiale" / "etablissements-scolaires-colleges.xlsx"
ELEMENTAIRES_RAW = BRONZE / "indice_vivabilite_familiale" / "etablissements-scolaires-ecoles-elementaires.xlsx"
MATERNELLES_RAW  = BRONZE / "indice_vivabilite_familiale" / "etablissements-scolaires-maternelles.xlsx"
# Indicator 2 — green spaces
ESPACES_VERTS_RAW = BRONZE / "indice_vivabilite_familiale" / "espaces_verts.geojson"
# DVF — housing transactions
DVF_RAW                 = BRONZE / "public_service_data" / "ValeursFoncieres-2025.txt"
# BDCOM — public service establishments
BDCOM_RAW               = BRONZE / "public_service_data" / "BDCOM_2023.csv"
BDCOM_OD_RAW            = BRONZE / "public_service_data" / "BDCOM_2023_OD.xlsx"
# Hospitals
HOSPITALS_RAW           = BRONZE / "public_service_data" / "les_etablissements_hospitaliers_franciliens.csv"
# Thermal confort
TREES_RAW               = BRONZE / "indice_confort_thermique" / "les-arbres.geojson"
ISLAND_OF_FRESHNESS_RAW = BRONZE / "indice_confort_thermique" / "ilots-de-fraicheur-espaces-verts-frais.geojson"

#indicator 2
TRANSPORT_ARRETS_RAW    = BRONZE / "transport_data" / "arrets.csv"
TRANSPORT_VELIB_RAW     = BRONZE / "transport_data" / "velib.csv"

# Sale price
SALE_PRICE_PDF          = BRONZE / "sale_price_data" / "HistoriquedesprixaumappartementsanciensParispararrdt_2.pdf"

# Rent price
QUARTIERS_KML           = BRONZE / "rent_data" / "L7501_zone_elem_2024.kml"
MAPPING_ZONES_XLSX      = BRONZE / "rent_data" / "table_zones_2024_L7501_1.xls"
RENT_DATA_CSV           = BRONZE / "rent_data" / "Base_OP_2024_L7501.csv"

# Share of population by SPC (Socio-professional category) in each IRIS
POP_DATA_SPC_RAW        = BRONZE / "pop_spc" / "base-ic-evol-struct-pop-2022.csv"
# demographics and socio-economics data
DEMO_REVENUE_BRONZE     = BRONZE / "demographics" / "BASE_TD_FILO_IRIS_2021_DEC.csv"
DEMO_CSP_BRONZE         = BRONZE / "demographics" / "base-ic-evol-struct-pop-2022.CSV"

# ── Silver outputs ─────────────────────────────────────────────────────────────
IRIS_SILVER       = SILVER / "iris_paris.csv"
POPULATION_SILVER = SILVER / "population_paris.csv"
SCHOOLS_SILVER    = SILVER / "schools_merged.csv"

DVF_SILVER        = SILVER / "dvf_paris_clean.csv"
BDCOM_SILVER      = SILVER / "bdcom_paris_clean.csv"
HOSPITALS_SILVER  = SILVER / "hospitals_paris_clean.csv"
ESPACES_VERTS_SILVER = SILVER / "espaces_verts_paris.geojson"

THERMAL_COMFORT_SILVER = SILVER / "thermal_comfort_base.geojson"
SALE_PRICE_SILVER = SILVER / "sale_price_m2.csv"
RENT_PRICE_SILVER = SILVER / "rent_data_complet.csv"

DEMO_SILVER       = SILVER / "demographics_paris.csv"

# ── DVF filter settings ────────────────────────────────────────────────────────
DVF_TYPES_TO_KEEP = ["Appartement", "Maison"]
DVF_SURFACE_MIN   = 5      # m²
DVF_SURFACE_MAX   = 1000   # m²
DVF_PRIX_M2_MIN   = 1_000  # €/m²
DVF_PRIX_M2_MAX   = 50_000 # €/m²

TRANSPORT_ARRETS_SILVER = SILVER / "transport_arrets_paris.csv"
TRANSPORT_VELIB_SILVER  = SILVER / "velib_paris.csv"


# ── Gold outputs ───────────────────────────────────────────────────────────────

BDCOM_GOLD      = GOLD / "bdcom.csv"
DVF_GOLD        = GOLD / "dvf.csv"
THERMAL_COMFORT_GOLD = GOLD / "urban_comfort_index.parquet"
SALE_PRICE_GOLD = GOLD / "sale_price_median.parquet"
RENT_PRICE_GOLD = GOLD / "rent_data_par_arrdt.parquet"

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
DEMO_GOLD                = GOLD / "demographics_gold.csv"

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
# Only pillars that vary by IRIS in Gold. Childcare, safety, and environment
# are still written to vivabilite_familiale (flat 5.0 placeholders) but are not
# part of vivabilite_score until real per-zone data exists.
VIVABILITE_WEIGHTS = {
    "school_score":         0.40,
    "healthcare_score":     0.30,
    "green_spaces_score":   0.15,
    "transport_score":      0.10,
    "daily_services_score": 0.05,
}

# ── Essential connectivity & services composite weights ───────────────────────
# These inputs are already normalised on the same 0–10 scale in Gold, so the
# composite is a direct weighted sum without an additional normalisation pass.
ESSENTIAL_CONNECTIVITY_WEIGHTS = {
    "transport_score":      1 / 3,
    "healthcare_score":     1 / 3,
    "daily_services_score": 1 / 3,
}
