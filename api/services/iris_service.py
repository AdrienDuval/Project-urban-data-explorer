"""Business logic for IRIS administrative zone queries."""

from __future__ import annotations

import threading
from typing import Optional

from cachetools import TTLCache, cached
from cachetools.keys import hashkey
from sqlalchemy import func, select

from api.db_models import school_density as sd
from api.models.common import PaginatedResponse
from api.models.iris import IrisZone
from src.db import SessionLocal

_cache = TTLCache(maxsize=300, ttl=3600)
_lock = threading.Lock()


def _row_to_iris_zone(row: dict) -> IrisZone:
    return IrisZone(
        code_iris=str(row["code_iris"]).zfill(9),
        name=row.get("LIBIRIS"),
        quarter_code=str(int(row["GRD_QUART"])) if row.get("GRD_QUART") is not None else None,
        arrondissement=row.get("LIBCOM"),
    )


@cached(cache=_cache, lock=_lock, key=lambda **kw: hashkey(**kw))
def list_iris_zones(
    *,
    arrondissement: Optional[str] = None,
    page: int = 1,
    size: int = 50,
) -> PaginatedResponse[IrisZone]:
    stmt = select(
        sd.c.code_iris, sd.c.LIBIRIS, sd.c.GRD_QUART, sd.c.LIBCOM
    )
    if arrondissement:
        stmt = stmt.where(sd.c.LIBCOM.ilike(f"%{arrondissement}%"))

    db = SessionLocal()
    try:
        total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        rows = db.execute(
            stmt.order_by(sd.c.code_iris).offset((page - 1) * size).limit(size)
        ).mappings().all()
    finally:
        db.close()

    pages = max(1, -(-total // size))
    return PaginatedResponse(
        items=[_row_to_iris_zone(dict(r)) for r in rows],
        total=total, page=page, size=size, pages=pages,
    )


@cached(cache=_cache, lock=_lock, key=lambda code_iris: hashkey("get", code_iris))
def get_iris_zone(code_iris: str) -> Optional[IrisZone]:
    code_iris = code_iris.zfill(9)
    stmt = select(sd.c.code_iris, sd.c.LIBIRIS, sd.c.GRD_QUART, sd.c.LIBCOM).where(
        sd.c.code_iris == code_iris
    )
    db = SessionLocal()
    try:
        row = db.execute(stmt).mappings().first()
    finally:
        db.close()
    return _row_to_iris_zone(dict(row)) if row else None
