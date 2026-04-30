"""SQLAlchemy Core table definitions mirroring the MySQL schema.

These are read-only Table objects — the API never writes to these tables.
The schema mirrors what was loaded by the ETL pipeline (run_pipeline.py).
"""
from __future__ import annotations

from sqlalchemy import BigInteger, Column, Float, Integer, MetaData, String, Table, Text

metadata = MetaData()

school_density = Table(
    "school_density",
    metadata,
    Column("IRIS", Text),
    Column("LAB_IRIS", BigInteger),
    Column("population", Float),
    Column("school_count", BigInteger),
    Column("schools_per_1000", Float),
    Column("school_score", Float),
    Column("code_iris", String(9)),
    Column("LIBCOM", Text),
    Column("LIBIRIS", Text),
    Column("GRD_QUART", BigInteger),
)

schools_ref = Table(
    "schools_ref",
    metadata,
    Column("name", Text),
    Column("address", Text),
    Column("arrondissement", Text),
    Column("code_insee", Text),
    Column("annee_scolaire", Text),
    Column("type", Text),
    Column("lat", Float),
    Column("lng", Float),
)

population_ref = Table(
    "population_ref",
    metadata,
    Column("IRIS", Text),
    Column("LAB_IRIS", BigInteger),
    Column("population", Float),
)

vivabilite_familiale = Table(
    "vivabilite_familiale",
    metadata,
    Column("IRIS", Text),
    Column("LIBCOM", Text),
    Column("LIBIRIS", Text),
    Column("GRD_QUART", BigInteger),
    Column("population", Float),
    Column("code_iris", Text),
    Column("school_count", BigInteger),
    Column("schools_per_1000", Float),
    Column("school_score", Float),
    Column("stop_count", BigInteger),
    Column("weighted_stops", Float),
    Column("transport_score", Float),
    Column("hospital_count", BigInteger),
    Column("service_count", BigInteger),
    Column("weighted_services", Float),
    Column("services_score", Float),
    Column("interior_m2", Float),
    Column("adjacent_m2", Float),
    Column("total_green_m2", Float),
    Column("green_m2_per_resident", Float),
    Column("green_spaces_score", Float),
    Column("healthcare_hospital_count", BigInteger),
    Column("weighted_hospital_count", Float),
    Column("healthcare_service_count", BigInteger),
    Column("weighted_healthcare_service_count", Float),
    Column("weighted_healthcare_access", Float),
    Column("healthcare_score", Float),
    Column("daily_service_count", BigInteger),
    Column("weighted_daily_service_count", Float),
    Column("daily_services_score", Float),
    Column("childcare_score", Float),
    Column("safety_score", Float),
    Column("environment_score", Float),
    Column("essential_connectivity_score", Float),
    Column("essential_connectivity_weights", Text),
    Column("vivabilite_score", Float),
    Column("vivabilite_model", Text),
    Column("vivabilite_weights", Text),
    Column("vivabilite_rank", BigInteger),
    Column("essential_connectivity_rank", BigInteger),
)

transport_score_iris = Table(
    "transport_score_iris",
    metadata,
    Column("CODE_IRIS", Text),
    Column("x_sum_weights", Float),
    Column("density_raw", Float),
    Column("density_score", Float),
    Column("weighted_mean_distance", Float),
    Column("proximity_score", Float),
    Column("transport_score", Float),
)

transport_points = Table(
    "transport_points",
    metadata,
    Column("id", BigInteger),
    Column("name", Text),
    Column("type", Text),
    Column("lat", Float),
    Column("lng", Float),
)

thermal_comfort = Table(
    "thermal_comfort",
    metadata,
    Column("code_iris", Text),
    Column("nom_iris", Text),
    Column("arrondissement", Text),
    Column("densite_arbres", Float),
    Column("ratio_fraicheur", Float),
    Column("tree_density_score", Float),
    Column("cooling_area_score", Float),
    Column("proximity_score", Float),
    Column("thermal_score", Float),
    Column("indice_confort_thermique", Float),
    Column("geometry", Text),
)

rent_data = Table(
    "rent_data",
    metadata,
    Column("n_sq_ar", Integer),
    Column("c_ar", Text),
    Column("c_arinsee", Integer),
    Column("l_ar", Text),
    Column("l_aroff", Text),
    Column("n_sq_co", Integer),
    Column("surface", Float),
    Column("perimetre", Float),
    Column("geom_x_y", Text),
    Column("geometry", Text),
    Column("loyer_median_m2", Float),
    Column("loyer_q1_m2", Float),
    Column("loyer_q3_m2", Float),
)

sale_price_median = Table(
    "sale_price_median",
    metadata,
    Column("n_sq_ar", Integer),
    Column("c_ar", Integer),
    Column("c_arinsee", Integer),
    Column("l_ar", Text),
    Column("l_aroff", Text),
    Column("n_sq_co", Integer),
    Column("surface", Float),
    Column("perimetre", Float),
    Column("geom_x_y", Text),
    Column("geometry", Text),
    Column("Trimestre", Text),
    Column("arrondissement", BigInteger),
    Column("prix_m2", BigInteger),
    Column("date_periode", Text),
)

demographics = Table(
    "demographics",
    metadata,
    Column("code_iris", Text),
    Column("nom_iris", Text),
    Column("population", Float),
    Column("pop_0_14", Float),
    Column("pop_15_29", Float),
    Column("pop_20_64", Float),
    Column("pop_65p", Float),
    Column("agriculteurs", Float),
    Column("artisans_commercants", Float),
    Column("cadres", Float),
    Column("professions_intermediaires", Float),
    Column("employes", Float),
    Column("ouvriers", Float),
    Column("retraites", Float),
    Column("sans_activite", Float),
    Column("pop_15p", Float),
    Column("pct_agriculteurs", Float),
    Column("pct_artisans_commercants", Float),
    Column("pct_cadres", Float),
    Column("pct_professions_intermediaires", Float),
    Column("pct_employes", Float),
    Column("pct_ouvriers", Float),
    Column("pct_retraites", Float),
    Column("pct_sans_activite", Float),
    Column("revenu_median", Float),
    Column("revenu_q1", Float),
    Column("revenu_q3", Float),
    Column("gini", Float),
    Column("taux_imposition", Float),
    Column("taux_pauvrete", Float),
    Column("score_revenus", Float),
    Column("score_mixite", Float),
    Column("demographics_score", Float),
)
