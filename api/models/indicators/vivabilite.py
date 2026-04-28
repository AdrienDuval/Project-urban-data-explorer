"""Pydantic models for the family liveability indicator (indice de vivabilité familiale).

The composite score is a non-price family suitability score combining schools,
childcare, safety, healthcare, environment, green spaces, transport, and daily
services. Childcare, safety, and environment may use a flat neutral sub-score
until per-IRIS data is available.
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
    ``vivabilite_rank`` and ``essential_connectivity_rank`` are 1 for the best
    zone in Paris for their respective scores.
    """

    code_iris: str = Field(description="9-digit INSEE IRIS code.")
    name: Optional[str] = Field(None, description="IRIS zone name.")
    arrondissement: Optional[str] = Field(None, description="Arrondissement label.")
    population: Optional[float] = Field(None, description="Resident population.")

    # Raw context and sub-scores (0–10)
    school_count: Optional[int] = Field(None, description="Schools within the analysis buffer.")
    schools_per_1000: Optional[float] = Field(None, description="Schools per 1,000 residents.")
    school_score: Optional[float] = Field(
        None, description="School accessibility score (0–10)."
    )
    childcare_score: Optional[float] = Field(None, description="Childcare score (0–10).")
    safety_score: Optional[float] = Field(None, description="Safety score (0–10).")
    healthcare_hospital_count: Optional[int] = Field(None, description="Hospitals near the IRIS zone.")
    healthcare_service_count: Optional[int] = Field(None, description="Pharmacy/medical BDCOM services near the IRIS zone.")
    weighted_healthcare_access: Optional[float] = Field(None, description="Weighted healthcare access count.")
    healthcare_score: Optional[float] = Field(None, description="Healthcare access score (0–10).")
    environment_score: Optional[float] = Field(None, description="Environment score (0–10).")
    transport_score: Optional[float] = Field(
        None, description="Transport accessibility score (0–10)."
    )
    stop_count: Optional[int] = Field(None, description="Transport points near the IRIS zone.")
    weighted_stops: Optional[float] = Field(None, description="Weighted transport stop count.")
    services_score: Optional[float] = Field(
        None, description="Legacy broad services proximity score (0–10)."
    )
    daily_service_count: Optional[int] = Field(None, description="Daily services near the IRIS zone.")
    weighted_daily_service_count: Optional[float] = Field(None, description="Weighted daily service count.")
    daily_services_score: Optional[float] = Field(None, description="Daily services score (0–10).")
    interior_m2: Optional[float] = Field(None, description="Green space area inside the IRIS.")
    adjacent_m2: Optional[float] = Field(None, description="Nearby green space area around the IRIS.")
    total_green_m2: Optional[float] = Field(None, description="Weighted accessible green space area.")
    green_m2_per_resident: Optional[float] = Field(None, description="Accessible green space per resident.")
    green_spaces_score: Optional[float] = Field(
        None, description="Green spaces per resident score (0–10)."
    )

    # Composite
    essential_connectivity_score: Optional[float] = Field(
        None,
        description=(
            "Composite essential connectivity and services score (0–10), "
            "combining transport, healthcare, and daily services."
        ),
    )
    essential_connectivity_rank: Optional[int] = Field(
        None, description="Rank among all Paris IRIS zones for essential connectivity (1 = best)."
    )
    essential_connectivity_weights: Optional[str] = Field(
        None, description="Serialized essential connectivity score weights."
    )
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
    vivabilite_model: Optional[str] = Field(None, description="Composite model identifier.")
    vivabilite_weights: Optional[str] = Field(None, description="Serialized official score weights.")


class VivabiliteArrondissementStats(BaseModel):
    """Aggregated family liveability statistics for one arrondissement."""

    arrondissement: str = Field(description="Arrondissement label.")
    iris_count: int = Field(description="Number of IRIS zones.")
    total_population: float = Field(description="Sum of resident populations.")
    avg_school_score: float = Field(description="Mean school score.")
    avg_childcare_score: float = Field(description="Mean childcare score.")
    avg_safety_score: float = Field(description="Mean safety score.")
    avg_healthcare_score: float = Field(description="Mean healthcare score.")
    avg_environment_score: float = Field(description="Mean environment score.")
    avg_transport_score: float = Field(description="Mean transport score.")
    avg_daily_services_score: float = Field(description="Mean daily services score.")
    avg_green_spaces_score: float = Field(description="Mean green spaces score.")
    avg_essential_connectivity_score: float = Field(description="Mean essential connectivity score.")
    avg_vivabilite_score: float = Field(description="Mean composite liveability score.")
    best_iris: Optional[str] = Field(None, description="IRIS zone name with the highest score.")
