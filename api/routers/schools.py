"""School-catalog endpoints."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from api.dependencies import PaginationDep
from api.models.common import PaginatedResponse
from api.models.schools import School
from api.services import schools_service

router = APIRouter()

_SCHOOL_TYPES = ["Collège", "Maternelle", "Elémentaire", "Polyvalent"]


@router.get("", response_model=PaginatedResponse[School], summary="List schools")
def list_schools(
    pagination: PaginationDep,
    school_type: Optional[str] = Query(None),
    arrondissement: Optional[str] = Query(None),
    name: Optional[str] = Query(None),
):
    if school_type and school_type not in _SCHOOL_TYPES:
        raise HTTPException(
            status_code=422,
            detail=f"Invalid school_type '{school_type}'. Must be one of: {', '.join(_SCHOOL_TYPES)}.",
        )
    return schools_service.list_schools(
        school_type=school_type, arrondissement=arrondissement, name=name, **pagination
    )


@router.get("/{school_id}", response_model=School, summary="Get school by ID")
def get_school(school_id: int):
    result = schools_service.get_school(school_id)
    if result is None:
        raise HTTPException(status_code=404, detail=f"School with id {school_id} not found.")
    return result
