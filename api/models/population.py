"""Pydantic models for population data responses.

Population figures come from the INSEE 2022 census (silver layer,
``population_paris.csv``).  Only residential IRIS zones (TYP_IRIS='H') with
more than 500 inhabitants are included.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class PopulationZone(BaseModel):
    """Census population for a single residential IRIS zone."""

    code_iris: str = Field(description="9-digit INSEE IRIS code.")
    arrondissement: str = Field(
        description="Arrondissement label (e.g. 'Paris 7e Arrondissement')."
    )
    name: str = Field(description="Human-readable IRIS zone name.")
    quarter_code: str = Field(description="GRD_QUART neighbourhood grouping code.")
    population: float = Field(
        description="Estimated resident population (INSEE 2019 census)."
    )
