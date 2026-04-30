from __future__ import annotations

import threading
from typing import Optional

from cachetools import TTLCache, cached
from cachetools.keys import hashkey
from sqlalchemy import func, select

from api.db_models import transport_points as tp
from api.db_models import transport_score_iris as tsi
from api.models.common import PaginatedResponse
from api.models.indicators.transport import TransportIndicator, TransportPoint
from src.db import SessionLocal

_cache = TTLCache(maxsize=300, ttl=1800)
_lock = threading.Lock()


def _row_to_indicator(row: dict) -> TransportIndicator:
    return TransportIndicator(
        code_iris=str(row["CODE_IRIS"]).zfill(9),
        x_sum_weights=float(row["x_sum_weights"]),
        density_score=float(row["density_score"]),
        proximity_score=float(row["proximity_score"]),
        transport_score=float(row["transport_score"]),
    )


def _row_to_point(row: dict) -> TransportPoint:
    return TransportPoint(
        id=str(row["id"]),
        name=str(row["name"]),
        type=str(row["type"]),
        lat=float(row["lat"]),
        lng=float(row["lng"]),
    )


@cached(cache=_cache, lock=_lock, key=lambda **kw: hashkey(**kw))
def list_transport_indicators(
    *,
    min_score: Optional[float] = None,
    max_score: Optional[float] = None,
    page: int = 1,
    size: int = 50,
) -> PaginatedResponse[TransportIndicator]:
    stmt = select(tsi)
    if min_score is not None:
        stmt = stmt.where(tsi.c.transport_score >= min_score)
    if max_score is not None:
        stmt = stmt.where(tsi.c.transport_score <= max_score)
    stmt = stmt.order_by(tsi.c.CODE_IRIS)

    db = SessionLocal()
    try:
        total = db.scalar(select(func.count()).select_from(stmt.subquery())) or 0
        rows = db.execute(stmt.offset((page - 1) * size).limit(size)).mappings().all()
    finally:
        db.close()

    pages = max(1, -(-total // size))
    return PaginatedResponse(
        items=[_row_to_indicator(dict(r)) for r in rows],
        total=total, page=page, size=size, pages=pages,
    )


@cached(cache=_cache, lock=_lock, key=lambda code_iris: hashkey("get", code_iris))
def get_transport_indicator(code_iris: str) -> Optional[TransportIndicator]:
    code_iris = code_iris.zfill(9)
    stmt = select(tsi).where(tsi.c.CODE_IRIS == code_iris)
    db = SessionLocal()
    try:
        row = db.execute(stmt).mappings().first()
    finally:
        db.close()
    return _row_to_indicator(dict(row)) if row else None


@cached(cache=_cache, lock=_lock, key=lambda type_filter=None: hashkey("points", type_filter))
def list_transport_points(*, type_filter: Optional[str] = None) -> list[TransportPoint]:
    stmt = select(tp)
    if type_filter:
        stmt = stmt.where(tp.c.type == type_filter.lower())
    db = SessionLocal()
    try:
        rows = db.execute(stmt).mappings().all()
    finally:
        db.close()
    return [_row_to_point(dict(r)) for r in rows]
