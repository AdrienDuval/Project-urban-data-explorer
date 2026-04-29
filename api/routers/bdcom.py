"""BDCOM commercial establishments endpoints.

All routes live under the ``/bdcom`` prefix (registered in ``main.py``).
"""

from __future__ import annotations

from fastapi import APIRouter

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
    "/by-type",
    summary="BDCOM establishments by commerce type",
    description=(
        "Return commercial establishments grouped by TYPE classification "
        "(e.g., restaurant, retail, office) with counts and surface statistics."
    ),
)
def get_bdcom_by_type(store: DataStoreDep):
    return bdcom_service.get_bdcom_by_type(store)

