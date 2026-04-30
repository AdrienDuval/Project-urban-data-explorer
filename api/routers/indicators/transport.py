from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, HTTPException, Query

from api.dependencies import PaginationDep
from api.models.common import PaginatedResponse
from api.models.indicators.transport import TransportIndicator, TransportPoint
from api.services.indicators import transport_service

router = APIRouter()


@router.get("", response_model=PaginatedResponse[TransportIndicator], summary="List transport scores by IRIS zone")
def list_transport_indicators(
    pagination: PaginationDep,
    min_score: Optional[float] = Query(None, ge=0, le=1),
    max_score: Optional[float] = Query(None, ge=0, le=1),
):
    return transport_service.list_transport_indicators(
        min_score=min_score, max_score=max_score, **pagination
    )


@router.get("/points", response_model=List[TransportPoint], summary="List all transport points")
def list_transport_points(
    type: Optional[str] = Query(None, description="Filter by type: metro, bus, tram, rail, velib"),
):
    return transport_service.list_transport_points(type_filter=type)


@router.get("/{code_iris}", response_model=TransportIndicator, summary="Transport score for a single IRIS zone")
def get_transport_indicator(code_iris: str):
    result = transport_service.get_transport_indicator(code_iris)
    if result is None:
        raise HTTPException(status_code=404, detail=f"IRIS zone '{code_iris}' not found.")
    return result
