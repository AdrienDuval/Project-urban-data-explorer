"""School-catalog endpoints.

All routes live under the ``/schools`` prefix (registered in ``main.py``).
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from api.dependencies import DataStoreDep, PaginationDep
from api.models.common import PaginatedResponse
from api.models.schools import School
from api.services import schools_service

router = APIRouter()

# Documented choices for the `type` filter
_SCHOOL_TYPES = ["Collège", "Maternelle", "Elémentaire", "Polyvalent"]


@router.get(
    "",
    response_model=PaginatedResponse[School],
    summary="List schools",
    description=(
        "Return a paginated list of schools from the silver-layer catalog.  "
        "Results can be filtered by school type, arrondissement, or a partial "
        "name search."
    ),
)
def list_schools(
    store: DataStoreDep,
    pagination: PaginationDep,
    school_type: Optional[str] = Query(
        None,
        description=(
            f"Filter by school type. One of: {', '.join(_SCHOOL_TYPES)}."
        ),
    ),
    arrondissement: Optional[str] = Query(
        None,
        description=(
            "Case-insensitive partial match on the arrondissement field "
            "(e.g. '9ème')."
        ),
    ),
    name: Optional[str] = Query(
        None,
        description="Case-insensitive partial match on the school name.",
    ),
):
    if school_type and school_type not in _SCHOOL_TYPES:
        raise HTTPException(
            status_code=422,
            detail=(
                f"Invalid school_type '{school_type}'. "
                f"Must be one of: {', '.join(_SCHOOL_TYPES)}."
            ),
        )
    return schools_service.list_schools(
        store,
        school_type=school_type,
        arrondissement=arrondissement,
        name=name,
        **pagination,
    )


@router.get(
    "/{school_id}",
    response_model=School,
    summary="Get school by ID",
    description=(
        "Return a single school by its integer catalog ID.  The ID corresponds "
        "to the row index in the silver-layer ``schools_merged.csv`` file."
    ),
)
def get_school(school_id: int, store: DataStoreDep):
    result = schools_service.get_school(store, school_id)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"School with id {school_id} not found.",
        )
    return result
