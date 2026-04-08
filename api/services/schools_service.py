"""Business logic for school-catalog queries."""

from __future__ import annotations

from typing import Optional

import pandas as pd

from api.models.common import PaginatedResponse
from api.models.schools import School
from api.services.data_loader import DataStore

# Valid school types sourced from the silver pipeline
VALID_TYPES = {"Collège", "Maternelle", "Elémentaire", "Polyvalent"}


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _row_to_school(idx: int, row: pd.Series) -> School:
    """Convert a DataFrame row into a ``School`` response model."""
    return School(
        id=int(idx),
        name=str(row["name"]),
        address=str(row["address"]),
        arrondissement=str(row["arrondissement"]),
        code_insee=str(row["code_insee"]),
        school_year=str(row["annee_scolaire"]),
        type=str(row["type"]),
        lat=float(row["lat"]),
        lng=float(row["lng"]),
    )


def _paginate(df: pd.DataFrame, page: int, size: int) -> tuple[pd.DataFrame, int]:
    total = len(df)
    offset = (page - 1) * size
    return df.iloc[offset : offset + size], total


# ---------------------------------------------------------------------------
# Public service functions
# ---------------------------------------------------------------------------

def list_schools(
    store: DataStore,
    *,
    school_type: Optional[str] = None,
    arrondissement: Optional[str] = None,
    name: Optional[str] = None,
    page: int = 1,
    size: int = 50,
) -> PaginatedResponse[School]:
    """Return a paginated, optionally filtered list of schools.

    Args:
        store:          Loaded DataStore.
        school_type:    Exact match against the ``type`` column.  Must be one of
                        Collège, Maternelle, Elémentaire, Polyvalent.
        arrondissement: Partial, case-insensitive match against the
                        ``arrondissement`` column (e.g. ``"9ème"``).
        name:           Partial, case-insensitive match against the school name.
        page:           1-based page number.
        size:           Page size (max enforced by the router).
    """
    df = store.schools.copy()

    if school_type:
        df = df[df["type"] == school_type]

    if arrondissement:
        df = df[
            df["arrondissement"].str.contains(arrondissement, case=False, na=False)
        ]

    if name:
        df = df[df["name"].str.contains(name, case=False, na=False)]

    page_df, total = _paginate(df, page, size)
    pages = max(1, -(-total // size))

    return PaginatedResponse(
        items=[_row_to_school(idx, row) for idx, row in page_df.iterrows()],
        total=total,
        page=page,
        size=size,
        pages=pages,
    )


def get_school(store: DataStore, school_id: int) -> Optional[School]:
    """Fetch a single school by its catalog index.

    Returns ``None`` when the id is out of range.
    """
    if school_id < 0 or school_id >= len(store.schools):
        return None
    row = store.schools.iloc[school_id]
    return _row_to_school(school_id, row)
