"""DVF housing transactions endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Path

from api.services import dvf_service

router = APIRouter()


@router.get("/stats", summary="DVF housing transaction statistics")
def get_dvf_stats():
    return dvf_service.get_dvf_stats()


@router.get("/by-year", summary="DVF transactions by year")
def get_dvf_by_year():
    return dvf_service.get_dvf_by_year()


@router.get("/by-iris/{code_iris}", summary="DVF transactions for an IRIS zone")
def get_dvf_by_iris(code_iris: str = Path(..., description="9-digit IRIS code")):
    return dvf_service.get_dvf_by_iris(code_iris)
