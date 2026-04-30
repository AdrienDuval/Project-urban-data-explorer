"""BDCOM commercial establishments endpoints.

All routes live under the ``/bdcom`` prefix (registered in ``main.py``).
"""

from __future__ import annotations

from fastapi import APIRouter, Path

from api.dependencies import DataStoreDep
from api.services import bdcom_service

router = APIRouter()


@router.get(
    "/stats",
    summary="BDCOM establishments statistics",
    description=(
        "Return aggregate statistics for commercial establishments in Paris: "
        "total count, surface distribution, top activities, and breakdown by arrondissement."
    ),
)
def get_bdcom_stats(store: DataStoreDep):
    return bdcom_service.get_bdcom_stats(store)


@router.get(
    "/by-iris/{code_iris}",
    summary="BDCOM establishments for an IRIS zone",
    description="Return commercial establishment statistics for a single 9-digit IRIS zone code.",
)
def get_bdcom_by_iris(
    store: DataStoreDep,
    code_iris: str = Path(..., description="9-digit IRIS code"),
):
    return bdcom_service.get_bdcom_by_iris(store, code_iris)


@router.get(
    "/by-type",
    summary="BDCOM establishments by commerce type",
    description=(
        "Return commercial establishments grouped by TYPE classification "
        "(e.g., restaurant, retail, office) with counts and surface statistics."
    ),
)
def get_bdcom_by_type(store: DataStoreDep):
    return bdcom_service.get_bdcom_by_type(store)

