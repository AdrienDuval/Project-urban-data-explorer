"""Business logic for the family liveability indicator (vivabilité familiale)."""

from __future__ import annotations

import threading
from typing import List, Optional

from cachetools import TTLCache, cached
from cachetools.keys import hashkey
from sqlalchemy import func, select

from api.db_models import vivabilite_familiale as vf
from api.models.common import PaginatedResponse
from api.models.indicators.vivabilite import (
    VivabiliteArrondissementStats,
    VivabiliteIndicator,
)
from src.db import SessionLocal

_cache = TTLCache(maxsize=500, ttl=1800)
_lock = threading.Lock()

_SCORE_COLS = [
    vf.c.school_score, vf.c.childcare_score, vf.c.safety_score,
    vf.c.healthcare_score, vf.c.environment_score, vf.c.transport_score,
    vf.c.daily_services_score, vf.c.green_spaces_score,
    vf.c.essential_connectivity_score, vf.c.vivabilite_score,
]


def _val(d: dict, key: str):
    v = d.get(key)
    return None if v is None else v


def _int_val(d: dict, key: str):
    v = _val(d, key)
    return int(v) if v is not None else None


def _row_to_indicator(row: dict) -> VivabiliteIndicator:
    return VivabiliteIndicator(
        code_iris=str(row.get("IRIS", "")).zfill(9),
        name=_val(row, "LIBIRIS"),
        arrondissement=_val(row, "LIBCOM"),
        population=_val(row, "population"),
        school_count=_int_val(row, "school_count"),
        schools_per_1000=_val(row, "schools_per_1000"),
        school_score=_val(row, "school_score"),
        childcare_score=_val(row, "childcare_score"),
        safety_score=_val(row, "safety_score"),
        healthcare_hospital_count=_int_val(row, "healthcare_hospital_count"),
        healthcare_service_count=_int_val(row, "healthcare_service_count"),
        weighted_healthcare_access=_val(row, "weighted_healthcare_access"),
        healthcare_score=_val(row, "healthcare_score"),
        environment_score=_val(row, "environment_score"),
        transport_score=_val(row, "transport_score"),
        stop_count=_int_val(row, "stop_count"),
        weighted_stops=_val(row, "weighted_stops"),
        services_score=_val(row, "services_score"),
        daily_service_count=_int_val(row, "daily_service_count"),
        weighted_daily_service_count=_val(row, "weighted_daily_service_count"),
        daily_services_score=_val(row, "daily_services_score"),
        interior_m2=_val(row, "interior_m2"),
        adjacent_m2=_val(row, "adjacent_m2"),
        total_green_m2=_val(row, "total_green_m2"),
        green_m2_per_resident=_val(row, "green_m2_per_resident"),
        green_spaces_score=_val(row, "green_spaces_score"),
        essential_connectivity_score=_val(row, "essential_connectivity_score"),
        essential_connectivity_rank=_int_val(row, "essential_connectivity_rank"),
        essential_connectivity_weights=_val(row, "essential_connectivity_weights"),
        vivabilite_score=_val(row, "vivabilite_score"),
        vivabilite_rank=_int_val(row, "vivabilite_rank"),
        vivabilite_model=_val(row, "vivabilite_model"),
        vivabilite_weights=_val(row, "vivabilite_weights"),
    )


@cached(cache=_cache, lock=_lock, key=lambda **kw: hashkey(**kw))
def list_vivabilite_indicators(
    *,
    arrondissement: Optional[str] = None,
    min_score: Optional[float] = None,
    max_score: Optional[float] = None,
    page: int = 1,
    size: int = 50,
) -> PaginatedResponse[VivabiliteIndicator]:
    stmt = select(vf)
    if arrondissement:
        stmt = stmt.where(vf.c.LIBCOM.ilike(f"%{arrondissement}%"))
    if min_score is not None:
        stmt = stmt.where(vf.c.vivabilite_score >= min_score)
    if max_score is not None:
        stmt = stmt.where(vf.c.vivabilite_score <= max_score)
    stmt = stmt.order_by(vf.c.vivabilite_rank)

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
def get_vivabilite_indicator(code_iris: str) -> Optional[VivabiliteIndicator]:
    code_iris = code_iris.zfill(9)
    stmt = select(vf).where(vf.c.IRIS == code_iris)
    db = SessionLocal()
    try:
        row = db.execute(stmt).mappings().first()
    finally:
        db.close()
    return _row_to_indicator(dict(row)) if row else None


@cached(cache=_cache, lock=_lock, key=lambda: hashkey("arrondissements"))
def list_vivabilite_arrondissements() -> List[VivabiliteArrondissementStats]:
    stmt = (
        select(
            vf.c.LIBCOM,
            func.count(vf.c.IRIS).label("iris_count"),
            func.sum(vf.c.population).label("total_population"),
            func.avg(vf.c.school_score).label("avg_school"),
            func.avg(vf.c.childcare_score).label("avg_childcare"),
            func.avg(vf.c.safety_score).label("avg_safety"),
            func.avg(vf.c.healthcare_score).label("avg_healthcare"),
            func.avg(vf.c.environment_score).label("avg_environment"),
            func.avg(vf.c.transport_score).label("avg_transport"),
            func.avg(vf.c.daily_services_score).label("avg_daily"),
            func.avg(vf.c.green_spaces_score).label("avg_green"),
            func.avg(vf.c.essential_connectivity_score).label("avg_essential"),
            func.avg(vf.c.vivabilite_score).label("avg_vivabilite"),
            func.max(vf.c.LIBIRIS).label("best_iris_name"),
        )
        .where(vf.c.LIBCOM.is_not(None))
        .group_by(vf.c.LIBCOM)
        .order_by(vf.c.LIBCOM)
    )
    db = SessionLocal()
    try:
        rows = db.execute(stmt).all()
    finally:
        db.close()

    return [
        VivabiliteArrondissementStats(
            arrondissement=str(r.LIBCOM),
            iris_count=int(r.iris_count),
            total_population=float(r.total_population or 0),
            avg_school_score=round(float(r.avg_school or 0), 2),
            avg_childcare_score=round(float(r.avg_childcare or 0), 2),
            avg_safety_score=round(float(r.avg_safety or 0), 2),
            avg_healthcare_score=round(float(r.avg_healthcare or 0), 2),
            avg_environment_score=round(float(r.avg_environment or 0), 2),
            avg_transport_score=round(float(r.avg_transport or 0), 2),
            avg_daily_services_score=round(float(r.avg_daily or 0), 2),
            avg_green_spaces_score=round(float(r.avg_green or 0), 2),
            avg_essential_connectivity_score=round(float(r.avg_essential or 0), 2),
            avg_vivabilite_score=round(float(r.avg_vivabilite or 0), 2),
            best_iris=str(r.best_iris_name) if r.best_iris_name else None,
        )
        for r in rows
    ]


def get_vivabilite_arrondissement(arrondissement: str) -> Optional[VivabiliteArrondissementStats]:
    query = arrondissement.lower()
    for s in list_vivabilite_arrondissements():
        if query in s.arrondissement.lower():
            return s
    return None
