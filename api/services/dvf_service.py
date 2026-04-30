"""Business logic for DVF housing transactions statistics.

The dvf MySQL table does not yet exist — these functions return empty data
until the pipeline populates it.
"""

from __future__ import annotations

_EMPTY_STATS = {
    "total_transactions": 0,
    "median_prix_m2": 0,
    "median_surface_m2": 0,
    "total_value": 0,
    "price_range": {"min": 0, "max": 0},
    "by_arrondissement": [],
    "by_type": [],
}


def get_dvf_stats() -> dict:
    return _EMPTY_STATS


def get_dvf_by_year() -> dict:
    return {}


def get_dvf_by_iris(code_iris: str) -> dict:
    return {
        "code_iris": code_iris,
        "total_transactions": 0,
        "median_prix_m2": 0,
        "median_surface_m2": 0,
        "total_value": 0,
        "price_range": {"min": 0, "max": 0},
        "by_year": {},
        "by_type": {},
    }
