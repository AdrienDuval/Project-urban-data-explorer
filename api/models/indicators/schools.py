"""Pydantic models for the school-accessibility indicator.

This indicator combines IRIS administrative data, census population, and the
school-density scores computed by the gold-layer pipeline.  It is the single
authoritative response shape for everything under ``/indicators/schools``.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class SchoolIndicator(BaseModel):
    """School-accessibility score for a single IRIS zone.

    Joins:
    - IRIS administrative metadata  (code, name, arrondissement)
    - INSEE 2019 census population
    - Gold-layer school-density metrics (count, rate per 1 000, normalised score)

    ``population``, ``schools_per_1000``, and ``school_score`` are ``None``
    for non-residential zones that were not matched during the spatial pipeline.
    """

    code_iris: str = Field(description="9-digit INSEE IRIS code.")
    name: Optional[str] = Field(None, description="Human-readable IRIS zone name.")
    quarter_code: Optional[str] = Field(
        None, description="GRD_QUART neighbourhood grouping code."
    )
    arrondissement: Optional[str] = Field(
        None, description="Arrondissement label (e.g. 'Paris 7e Arrondissement')."
    )
    # --- census ---
    population: Optional[float] = Field(
        None, description="Estimated resident population (INSEE 2019 census)."
    )
    # --- school metrics ---
    school_count: int = Field(
        description="Number of schools within a 500 m buffer of this zone."
    )
    schools_per_1000: Optional[float] = Field(
        None,
        description="Schools per 1 000 residents. Null when population data is unavailable.",
    )
    school_score: Optional[float] = Field(
        None,
        description=(
            "Normalised school-accessibility score from 0 (lowest) to 100 (highest), "
            "computed relative to all Paris IRIS zones."
        ),
    )


class SchoolArrondissementStats(BaseModel):
    """Aggregated school-accessibility statistics for one arrondissement.

    Computed by grouping all residential IRIS zones belonging to the same
    arrondissement and summarising their population and school metrics.
    """

    arrondissement: str = Field(description="Arrondissement label.")
    iris_count: int = Field(description="Number of residential IRIS zones.")
    total_population: float = Field(description="Sum of resident populations.")
    total_schools: int = Field(
        description="Total school count across all IRIS zones (500 m buffer)."
    )
    avg_schools_per_1000: float = Field(
        description="Population-weighted average schools per 1 000 residents."
    )
    avg_school_score: float = Field(
        description="Mean school-accessibility score across zones."
    )
