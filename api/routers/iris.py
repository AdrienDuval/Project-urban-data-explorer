"""IRIS administrative zone endpoints.

All routes live under the ``/iris`` prefix (registered in ``main.py``).

These endpoints return *only* geographic / administrative data.
For population figures use ``/population``.
For indicator scores use ``/indicators/schools`` (and future indicator prefixes).
"""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from api.dependencies import DataStoreDep, PaginationDep
from api.models.common import PaginatedResponse
from api.models.iris import IrisZone
from api.services import iris_service

router = APIRouter()


@router.get(
    "",
    response_model=PaginatedResponse[IrisZone],
    summary="List IRIS zones",
    description=(
        "Return a paginated list of Paris IRIS zones with administrative "
        "metadata only (code, name, quarter, arrondissement).  "
        "For population data see ``/population``.  "
        "For school scores see ``/indicators/schools``."
    ),
)
def list_iris_zones(
    store: DataStoreDep,
    pagination: PaginationDep,
    arrondissement: Optional[str] = Query(
        None,
        description=(
            "Case-insensitive partial match on the arrondissement name "
            "(e.g. '7e' matches 'Paris 7e Arrondissement')."
        ),
    ),
):
    return iris_service.list_iris_zones(
        store, arrondissement=arrondissement, **pagination
    )


@router.get(
    "/{code_iris}",
    response_model=IrisZone,
    summary="Get IRIS zone",
    description=(
        "Return administrative metadata for a single IRIS zone identified by "
        "its 9-digit INSEE code."
    ),
)
def get_iris_zone(code_iris: str, store: DataStoreDep):
    result = iris_service.get_iris_zone(store, code_iris)
    if result is None:
        raise HTTPException(
            status_code=404,
            detail=f"IRIS zone '{code_iris}' not found.",
        )
    return result
