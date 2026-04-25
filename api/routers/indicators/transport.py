from __future__ import annotations
from typing import List, Optional
from fastapi import APIRouter, HTTPException, Query
from api.dependencies import DataStoreDep, PaginationDep
from api.models.common import PaginatedResponse
from api.models.indicators.transport import TransportIndicator, TransportPoint
from api.services.indicators import transport_service

router = APIRouter()


@router.get(
    "",
    response_model=PaginatedResponse[TransportIndicator],
    summary="List transport scores by IRIS zone",
)
def list_transport_indicators(
    store: DataStoreDep,
    pagination: PaginationDep,
    min_score: Optional[float] = Query(None, ge=0, le=1),
    max_score: Optional[float] = Query(None, ge=0, le=1),
):
    return transport_service.list_transport_indicators(
        store, min_score=min_score, max_score=max_score, **pagination
    )


@router.get(
    "/points",
    response_model=List[TransportPoint],
    summary="List all transport points (stops + Vélib stations)",
)
def list_transport_points(
    store: DataStoreDep,
    type: Optional[str] = Query(None, description="Filter by type: metro, bus, tram, rail, velib"),
):
    return transport_service.list_transport_points(store, type_filter=type)


@router.get(
    "/{code_iris}",
    response_model=TransportIndicator,
    summary="Transport score for a single IRIS zone",
)
def get_transport_indicator(code_iris: str, store: DataStoreDep):
    result = transport_service.get_transport_indicator(store, code_iris)
    if result is None:
        raise HTTPException(status_code=404, detail=f"IRIS zone '{code_iris}' not found.")
    return result