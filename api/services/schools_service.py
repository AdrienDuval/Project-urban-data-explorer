"""Business logic for school-catalog queries."""

from __future__ import annotations

import threading
from typing import Optional

from cachetools import TTLCache, cached
from cachetools.keys import hashkey
from sqlalchemy import func, select

from api.db_models import schools_ref as sr
from api.models.common import PaginatedResponse
from api.models.schools import School
from src.db import SessionLocal

_cache = TTLCache(maxsize=500, ttl=3600)
_lock = threading.Lock()

_ORDER_BY = [sr.c.name, sr.c.address]


def _row_to_school(row_id: int, row: dict) -> School:
    return School(
        id=row_id,
        name=str(row["name"]),
        address=str(row["address"]),
        arrondissement=str(row["arrondissement"]),
        code_insee=str(row["code_insee"]),
        school_year=str(row["annee_scolaire"]),
        type=str(row["type"]),
        lat=float(row["lat"]),
        lng=float(row["lng"]),
    )


def _base_stmt(
    school_type: Optional[str],
    arrondissement: Optional[str],
    name: Optional[str],
):
    stmt = select(sr)
    if school_type:
        stmt = stmt.where(sr.c.type == school_type)
    if arrondissement:
        stmt = stmt.where(sr.c.arrondissement.ilike(f"%{arrondissement}%"))
    if name:
        stmt = stmt.where(sr.c.name.ilike(f"%{name}%"))
    return stmt.order_by(*_ORDER_BY)


@cached(cache=_cache, lock=_lock, key=lambda **kw: hashkey(**kw))
def list_schools(
    *,
    school_type: Optional[str] = None,
    arrondissement: Optional[str] = None,
    name: Optional[str] = None,
    page: int = 1,
    size: int = 50,
) -> PaginatedResponse[School]:
    stmt = _base_stmt(school_type, arrondissement, name)
    offset = (page - 1) * size

    db = SessionLocal()
    try:
        total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        rows = db.execute(stmt.offset(offset).limit(size)).mappings().all()
    finally:
        db.close()

    items = [_row_to_school(offset + i, dict(r)) for i, r in enumerate(rows)]
    pages = max(1, -(-total // size))
    return PaginatedResponse(items=items, total=total, page=page, size=size, pages=pages)


@cached(cache=_cache, lock=_lock, key=lambda school_id: hashkey("get", school_id))
def get_school(school_id: int) -> Optional[School]:
    stmt = select(sr).order_by(*_ORDER_BY).offset(school_id).limit(1)
    db = SessionLocal()
    try:
        row = db.execute(stmt).mappings().first()
    finally:
        db.close()
    return _row_to_school(school_id, dict(row)) if row else None
