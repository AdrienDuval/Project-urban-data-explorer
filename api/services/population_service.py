"""Business logic for population queries."""

from __future__ import annotations

import threading
from typing import Optional

from cachetools import TTLCache, cached
from cachetools.keys import hashkey
from sqlalchemy import func, select

from api.db_models import population_ref as pr
from api.db_models import school_density as sd
from api.models.common import PaginatedResponse
from api.models.population import PopulationZone
from src.db import SessionLocal

_cache = TTLCache(maxsize=300, ttl=3600)
_lock = threading.Lock()


def _row_to_zone(row: dict) -> PopulationZone:
    return PopulationZone(
        code_iris=str(row["IRIS"]).zfill(9),
        arrondissement=str(row.get("LIBCOM") or ""),
        name=str(row.get("LIBIRIS") or row.get("LAB_IRIS") or ""),
        quarter_code=str(row.get("GRD_QUART") or ""),
        population=float(row["population"]),
    )


def _enriched_stmt(arrondissement: Optional[str]):
    """JOIN population_ref with school_density to get LIBCOM/LIBIRIS/GRD_QUART."""
    stmt = (
        select(
            pr.c.IRIS,
            pr.c.population,
            sd.c.LIBCOM,
            sd.c.LIBIRIS,
            sd.c.GRD_QUART,
        )
        .outerjoin(sd, pr.c.IRIS == sd.c.code_iris)
        .order_by(pr.c.IRIS)
    )
    if arrondissement:
        stmt = stmt.where(sd.c.LIBCOM.ilike(f"%{arrondissement}%"))
    return stmt


@cached(cache=_cache, lock=_lock, key=lambda **kw: hashkey(**kw))
def list_population_zones(
    *,
    arrondissement: Optional[str] = None,
    page: int = 1,
    size: int = 50,
) -> PaginatedResponse[PopulationZone]:
    stmt = _enriched_stmt(arrondissement)

    db = SessionLocal()
    try:
        total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        rows = db.execute(stmt.offset((page - 1) * size).limit(size)).mappings().all()
    finally:
        db.close()

    pages = max(1, -(-total // size))
    return PaginatedResponse(
        items=[_row_to_zone(dict(r)) for r in rows],
        total=total, page=page, size=size, pages=pages,
    )


@cached(cache=_cache, lock=_lock, key=lambda code_iris: hashkey("get", code_iris))
def get_population_zone(code_iris: str) -> Optional[PopulationZone]:
    code_iris = code_iris.zfill(9)
    stmt = (
        select(pr.c.IRIS, pr.c.population, sd.c.LIBCOM, sd.c.LIBIRIS, sd.c.GRD_QUART)
        .outerjoin(sd, pr.c.IRIS == sd.c.code_iris)
        .where(pr.c.IRIS == code_iris)
    )
    db = SessionLocal()
    try:
        row = db.execute(stmt).mappings().first()
    finally:
        db.close()
    return _row_to_zone(dict(row)) if row else None
