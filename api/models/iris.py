"""Pydantic models for IRIS administrative zone responses.

These models carry *only* geographic and administrative metadata.
Population figures live in ``api/models/population.py``.
Indicator results (schools, …) live under ``api/models/indicators/``.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field


class IrisZone(BaseModel):
    """A single IRIS administrative zone (geographic / administrative data only).

    IRIS (Ilots Regroupés pour l'Information Statistique) is the finest
    granularity used by INSEE — roughly equivalent to a neighbourhood of
    2 000 inhabitants.

    Fields marked Optional are absent for non-residential zones (TYP_IRIS ≠ 'H')
    that appear in the geometry file but are not matched to census data.
    """

    code_iris: str = Field(description="9-digit INSEE IRIS code (e.g. '751010101').")
    name: Optional[str] = Field(None, description="Human-readable IRIS zone name.")
    quarter_code: Optional[str] = Field(
        None, description="GRD_QUART grouping code for the neighbourhood."
    )
    arrondissement: Optional[str] = Field(
        None, description="Arrondissement label (e.g. 'Paris 7e Arrondissement')."
    )
