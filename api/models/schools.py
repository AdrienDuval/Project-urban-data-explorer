"""Pydantic models for school catalog responses."""

from __future__ import annotations

from pydantic import BaseModel, Field


class School(BaseModel):
    """A single school entry from the silver-layer catalog.

    The catalog is built by merging the three official Île-de-France school
    datasets (colleges, elementaires, maternelles) and deduplicating by
    (name, address), keeping the most recent school year.
    """

    id: int = Field(description="Row index within the school catalog (0-based).")
    name: str = Field(description="School name.")
    address: str = Field(description="Street address.")
    arrondissement: str = Field(
        description="Arrondissement label (e.g. '9ème Ardt')."
    )
    code_insee: str = Field(
        description="5-digit INSEE commune code (e.g. '75109' for Paris 9th)."
    )
    school_year: str = Field(
        description="Most recent school year the establishment appears in (e.g. '2026-2027')."
    )
    type: str = Field(
        description="School type: Collège, Maternelle, Elémentaire, or Polyvalent."
    )
    lat: float = Field(description="WGS-84 latitude.")
    lng: float = Field(description="WGS-84 longitude.")
