"""FastAPI dependency-injection helpers."""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Query

from api.services.data_loader import DataStore
from api.services.spatial_cache import SpatialStore, get_spatial_store


# ---------------------------------------------------------------------------
# DataStore injection (legacy — only used by bdcom/dvf routers)
# ---------------------------------------------------------------------------

def _get_data_store() -> DataStore:
    return DataStore.load()


DataStoreDep = Annotated[DataStore, Depends(_get_data_store)]


# ---------------------------------------------------------------------------
# SpatialStore injection (map layers with geometry)
# ---------------------------------------------------------------------------

SpatialStoreDep = Annotated[SpatialStore, Depends(get_spatial_store)]


# ---------------------------------------------------------------------------
# Pagination query parameters
# ---------------------------------------------------------------------------

def _pagination_params(
    page: int = Query(1, ge=1, description="Page number (1-based)."),
    size: int = Query(50, ge=1, le=200, description="Items per page (max 200)."),
) -> dict:
    return {"page": page, "size": size}


PaginationDep = Annotated[dict, Depends(_pagination_params)]
