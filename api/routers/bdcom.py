"""BDCOM commercial establishments endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Path

from api.services import bdcom_service

router = APIRouter()


@router.get("/stats", summary="BDCOM establishments statistics")
def get_bdcom_stats():
    return bdcom_service.get_bdcom_stats()


@router.get("/by-type", summary="BDCOM establishments by commerce type")
def get_bdcom_by_type():
    return bdcom_service.get_bdcom_by_type()


@router.get("/by-iris/{code_iris}", summary="BDCOM establishments for an IRIS zone")
def get_bdcom_by_iris(code_iris: str = Path(..., description="9-digit IRIS code")):
    return bdcom_service.get_bdcom_by_iris(code_iris)
