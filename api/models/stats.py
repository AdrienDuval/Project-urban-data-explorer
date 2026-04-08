"""Pydantic models for city-wide statistics responses."""

from __future__ import annotations

from pydantic import BaseModel, Field


class SchoolTypeCount(BaseModel):
    """Count of schools for a single school type."""

    type: str = Field(description="School type label.")
    count: int = Field(description="Number of schools of this type.")


class CityStats(BaseModel):
    """High-level statistics for the entire Paris school-accessibility index.

    Useful as a quick sanity-check and for populating a dashboard header.
    """

    total_iris_zones: int = Field(
        description="Total number of IRIS zones in the dataset."
    )
    residential_iris_zones: int = Field(
        description="IRIS zones that have population data (TYP_IRIS='H')."
    )
    total_schools: int = Field(description="Total schools in the silver catalog.")
    school_types: list[SchoolTypeCount] = Field(
        description="Breakdown of the school catalog by type."
    )
    avg_schools_per_1000: float = Field(
        description="City-wide population-weighted average schools per 1 000 residents."
    )
    avg_school_score: float = Field(
        description="Mean school-accessibility score across all residential IRIS zones."
    )
    max_school_score: float = Field(
        description="Highest school-accessibility score in Paris."
    )
    min_school_score: float = Field(
        description="Lowest school-accessibility score in Paris."
    )
