"""Business logic for the school-accessibility indicator."""

from __future__ import annotations

import threading
from typing import Optional

from cachetools import TTLCache, cached
from cachetools.keys import hashkey
from sqlalchemy import func, select

from api.db_models import school_density as sd
from api.models.common import PaginatedResponse
from api.models.indicators.schools import SchoolArrondissementStats, SchoolIndicator
from src.db import SessionLocal

_cache = TTLCache(maxsize=500, ttl=1800)
_lock = threading.Lock()


def _row_to_indicator(row: dict) -> SchoolIndicator:
    return SchoolIndicator(
        code_iris=str(row["code_iris"]).zfill(9),
        name=row.get("LIBIRIS"),
        quarter_code=str(int(row["GRD_QUART"])) if row.get("GRD_QUART") is not None else None,
        arrondissement=row.get("LIBCOM"),
        population=row.get("population"),
        school_count=int(row["school_count"]) if row.get("school_count") is not None else 0,
        schools_per_1000=row.get("schools_per_1000"),
        school_score=row.get("school_score"),
    )


def _base_stmt(arrondissement, min_score, max_score):
    stmt = select(sd)
    if arrondissement:
        stmt = stmt.where(sd.c.LIBCOM.ilike(f"%{arrondissement}%"))
    if min_score is not None:
        stmt = stmt.where(sd.c.school_score >= min_score)
    if max_score is not None:
        stmt = stmt.where(sd.c.school_score <= max_score)
    return stmt.order_by(sd.c.code_iris)


@cached(cache=_cache, lock=_lock, key=lambda **kw: hashkey(**kw))
def list_school_indicators(
    *,
    arrondissement: Optional[str] = None,
    min_score: Optional[float] = None,
    max_score: Optional[float] = None,
    page: int = 1,
    size: int = 50,
) -> PaginatedResponse[SchoolIndicator]:
    stmt = _base_stmt(arrondissement, min_score, max_score)

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


@cached(cache=_cache, lock=_lock, key=lambda: hashkey("arrondissements"))
def list_school_arrondissements() -> list[SchoolArrondissementStats]:
    stmt = (
        select(
            sd.c.LIBCOM,
            func.count(sd.c.code_iris).label("iris_count"),
            func.sum(sd.c.population).label("total_population"),
            func.sum(sd.c.school_count).label("total_schools"),
            func.avg(sd.c.schools_per_1000).label("avg_per_1000"),
            func.avg(sd.c.school_score).label("avg_score"),
            func.sum(sd.c.schools_per_1000 * sd.c.population).label("weighted_sum"),
        )
        .where(
            sd.c.LIBCOM.is_not(None),
            sd.c.population.is_not(None),
            sd.c.school_score.is_not(None),
        )
        .group_by(sd.c.LIBCOM)
        .order_by(sd.c.LIBCOM)
    )
    db = SessionLocal()
    try:
        rows = db.execute(stmt).all()
    finally:
        db.close()

    results = []
    for r in rows:
        total_pop = float(r.total_population or 0)
        weighted = float(r.weighted_sum or 0)
        avg_per_1000 = round(weighted / total_pop, 4) if total_pop > 0 else 0.0
        results.append(
            SchoolArrondissementStats(
                arrondissement=str(r.LIBCOM),
                iris_count=int(r.iris_count),
                total_population=round(total_pop, 2),
                total_schools=int(r.total_schools or 0),
                avg_schools_per_1000=avg_per_1000,
                avg_school_score=round(float(r.avg_score or 0), 4),
            )
        )
    return results


@cached(cache=_cache, lock=_lock, key=lambda code_iris: hashkey("get", code_iris))
def get_school_indicator(code_iris: str) -> Optional[SchoolIndicator]:
    code_iris = code_iris.zfill(9)
    stmt = select(sd).where(sd.c.code_iris == code_iris)
    db = SessionLocal()
    try:
        row = db.execute(stmt).mappings().first()
    finally:
        db.close()
    return _row_to_indicator(dict(row)) if row else None


def get_school_arrondissement(arrondissement: str) -> Optional[SchoolArrondissementStats]:
    query = arrondissement.lower()
    matches = [s for s in list_school_arrondissements() if query in s.arrondissement.lower()]
    return matches[0] if matches else None
