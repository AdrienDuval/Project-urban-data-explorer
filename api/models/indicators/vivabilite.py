"""Pydantic models for the family liveability indicator (indice de vivabilité familiale).

The composite score combines four sub-indicators — schools, transport,
services, and green spaces — each normalised 0–10 and weighted equally.
The final vivabilite_score is also 0–10.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class VivabiliteIndicator(BaseModel):
    """Family liveability score for a single IRIS zone.

    Sub-scores:
        school_score        — school accessibility within 500 m (25 %)
        transport_score     — weighted public-transport stops within 500 m (25 %)
        services_score      — hospitals + essential services within 500 m (25 %)
        green_spaces_score  — usable green space per resident (25 %)

    All sub-scores and the composite are normalised 0–10 (higher = better).
    ``vivabilite_rank`` is 1 for the best zone in Paris.
    """

    code_iris: str = Field(description="9-digit INSEE IRIS code.")
    name: Optional[str] = Field(None, description="IRIS zone name.")
    arrondissement: Optional[str] = Field(None, description="Arrondissement label.")
    population: Optional[float] = Field(None, description="Resident population.")

    # Sub-scores (0–10)
    school_score: Optional[float] = Field(
        None, description="School accessibility score (0–10)."
    )
    transport_score: Optional[float] = Field(
        None, description="Transport accessibility score (0–10)."
    )
    services_score: Optional[float] = Field(
        None, description="Services proximity score (0–10)."
    )
    green_spaces_score: Optional[float] = Field(
        None, description="Green spaces per resident score (0–10)."
    )

    # Composite
    vivabilite_score: Optional[float] = Field(
        None,
        description=(
            "Composite family liveability score (0–10). "
            "Equal-weighted average of the four sub-scores."
        ),
    )
    vivabilite_rank: Optional[int] = Field(
        None, description="Rank among all Paris IRIS zones (1 = best)."
    )


class VivabiliteArrondissementStats(BaseModel):
    """Aggregated family liveability statistics for one arrondissement."""

    arrondissement: str = Field(description="Arrondissement label.")
    iris_count: int = Field(description="Number of IRIS zones.")
    total_population: float = Field(description="Sum of resident populations.")
    avg_school_score: float = Field(description="Mean school score.")
    avg_transport_score: float = Field(description="Mean transport score.")
    avg_services_score: float = Field(description="Mean services score.")
    avg_green_spaces_score: float = Field(description="Mean green spaces score.")
    avg_vivabilite_score: float = Field(description="Mean composite liveability score.")
    best_iris: Optional[str] = Field(None, description="IRIS zone name with the highest score.")
