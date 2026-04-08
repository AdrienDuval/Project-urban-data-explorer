"""FastAPI dependency-injection helpers.

Import these ``Annotated`` aliases in routers instead of writing the full
``Depends(...)`` expressions by hand.  This keeps routers concise and makes
swapping the backing store trivial in tests.
"""

from __future__ import annotations

from typing import Annotated

from fastapi import Depends, Query, Request

from api.services.data_loader import DataStore


# ---------------------------------------------------------------------------
# DataStore injection
# ---------------------------------------------------------------------------

def _get_data_store(request: Request) -> DataStore:
    """Extract the DataStore loaded at startup from ``app.state``."""
    return request.app.state.data


DataStoreDep = Annotated[DataStore, Depends(_get_data_store)]


# ---------------------------------------------------------------------------
# Pagination query parameters
# ---------------------------------------------------------------------------

def _pagination_params(
    page: int = Query(1, ge=1, description="Page number (1-based)."),
    size: int = Query(50, ge=1, le=200, description="Items per page (max 200)."),
) -> dict:
    return {"page": page, "size": size}


PaginationDep = Annotated[dict, Depends(_pagination_params)]
