"""IRIS administrative zone endpoints."""

from __future__ import annotations

from typing import Optional

from fastapi import APIRouter, HTTPException, Query

from api.dependencies import PaginationDep
from api.models.common import PaginatedResponse
from api.models.iris import IrisZone
from api.services import iris_service

router = APIRouter()


@router.get("", response_model=PaginatedResponse[IrisZone], summary="List IRIS zones")
def list_iris_zones(
    pagination: PaginationDep,
    arrondissement: Optional[str] = Query(None),
):
    return iris_service.list_iris_zones(arrondissement=arrondissement, **pagination)


@router.get("/{code_iris}", response_model=IrisZone, summary="Get IRIS zone")
def get_iris_zone(code_iris: str):
    result = iris_service.get_iris_zone(code_iris)
    if result is None:
        raise HTTPException(status_code=404, detail=f"IRIS zone '{code_iris}' not found.")
    return result
