"""Shared response models used across multiple routers."""

from __future__ import annotations

from typing import Generic, List, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic wrapper for paginated list responses.

    All list endpoints return this shape so clients can reliably handle
    pagination without inspecting each endpoint separately.
    """

    items: List[T] = Field(description="Current page of results.")
    total: int = Field(description="Total number of matching records.")
    page: int = Field(description="Current page number (1-based).")
    size: int = Field(description="Maximum items per page.")
    pages: int = Field(description="Total number of pages.")
