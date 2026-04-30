"""DVF housing transactions endpoints."""

from __future__ import annotations

from fastapi import APIRouter

from api.services import dvf_service

router = APIRouter()


@router.get("/stats", summary="DVF housing transaction statistics")
def get_dvf_stats():
    return dvf_service.get_dvf_stats()


@router.get("/by-year", summary="DVF transactions by year")
def get_dvf_by_year():
    return dvf_service.get_dvf_by_year()
