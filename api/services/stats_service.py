"""Business logic for city-wide statistics."""

from __future__ import annotations

import threading

from cachetools import TTLCache, cached
from sqlalchemy import func, select

from api.db_models import school_density as sd
from api.db_models import schools_ref as sr
from api.models.stats import CityStats, SchoolTypeCount
from src.db import SessionLocal

_cache = TTLCache(maxsize=10, ttl=1800)
_lock = threading.Lock()


@cached(cache=_cache, lock=_lock, key=lambda: "city_stats")
def get_city_stats() -> CityStats:
    db = SessionLocal()
    try:
        # Total iris zones and residential zones (population + school_score both non-null)
        total_iris = db.scalar(select(func.count()).select_from(sd)) or 0
        residential_q = select(func.count()).select_from(sd).where(
            sd.c.population.is_not(None),
            sd.c.school_score.is_not(None),
        )
        residential_iris = db.scalar(residential_q) or 0

        # Population-weighted average schools per 1 000
        weighted_q = select(
            func.sum(sd.c.schools_per_1000 * sd.c.population),
            func.sum(sd.c.population),
            func.avg(sd.c.school_score),
            func.max(sd.c.school_score),
            func.min(sd.c.school_score),
        ).where(
            sd.c.population.is_not(None),
            sd.c.school_score.is_not(None),
        )
        wrow = db.execute(weighted_q).first()
        weighted_sum, total_pop, avg_score, max_score, min_score = wrow or (0, 0, 0, 0, 0)
        avg_per_1000 = round(float(weighted_sum / total_pop), 4) if total_pop else 0.0

        # Total schools and type breakdown
        total_schools = db.scalar(select(func.count()).select_from(sr)) or 0
        type_rows = db.execute(
            select(sr.c.type, func.count(sr.c.type).label("cnt"))
            .group_by(sr.c.type)
            .order_by(func.count(sr.c.type).desc())
        ).all()
        school_types = [SchoolTypeCount(type=str(r.type), count=int(r.cnt)) for r in type_rows]
    finally:
        db.close()

    return CityStats(
        total_iris_zones=total_iris,
        residential_iris_zones=residential_iris,
        total_schools=total_schools,
        school_types=school_types,
        avg_schools_per_1000=avg_per_1000,
        avg_school_score=round(float(avg_score or 0), 4),
        max_school_score=round(float(max_score or 0), 4),
        min_school_score=round(float(min_score or 0), 4),
    )
