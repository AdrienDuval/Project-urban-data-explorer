"""
Silver → Gold (reference tables): schools and population

Schools and population are not computed indicators — they are reference data
needed by the map layer (school point markers, population choropleth).
This Gold step simply promotes them from Silver files into the shared DB,
making them available to the API and the Mapbox frontend without any
transformation beyond what Silver already applied.

Tables written:
    schools_ref   — school points with lat/lng for map markers
    population_ref — IRIS population for choropleth colouring
"""
import pandas as pd

from src.config import POPULATION_SILVER, SCHOOLS_SILVER
from src.db import engine


def load_reference_tables() -> None:
    """
    Write Silver schools and population to Gold DB tables.

    These are consumed by:
    - Mapbox school point layer  → schools_ref (lat, lng, name, type)
    - Mapbox population choropleth → population_ref (IRIS, population)
    - API /schools and /population endpoints (once migrated to DB reads)
    """
    schools = pd.read_csv(SCHOOLS_SILVER, dtype={"code_insee": str})
    schools.to_sql("schools_ref", engine, if_exists="replace", index=False)
    print(f"[reference] {len(schools)} schools → DB:schools_ref")

    population = pd.read_csv(POPULATION_SILVER, dtype={"IRIS": str})
    population["IRIS"] = population["IRIS"].str.zfill(9)
    population.to_sql("population_ref", engine, if_exists="replace", index=False)
    print(f"[reference] {len(population)} IRIS zones → DB:population_ref")
