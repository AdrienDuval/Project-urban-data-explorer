"""Business logic for BDCOM commercial establishments statistics.

The bdcom MySQL table does not yet exist — these functions return empty data
until the pipeline populates it.
"""

from __future__ import annotations


def get_bdcom_stats() -> dict:
    return {
        "total_establishments": 0,
        "total_surface_m2": 0,
        "avg_surface_m2": 0,
        "top_activities": [],
        "by_arrondissement": [],
    }


def get_bdcom_by_type() -> dict:
    return {}
