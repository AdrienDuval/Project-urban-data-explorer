"""Business logic for city-wide statistics."""

from __future__ import annotations

import pandas as pd

from api.models.stats import CityStats, SchoolTypeCount
from api.services.data_loader import DataStore


def get_city_stats(store: DataStore) -> CityStats:
    """Compute summary statistics for the entire Paris school-accessibility index.

    Residential zones are those with non-null population **and** school_score
    values — i.e. zones that were matched in the spatial join pipeline.
    """
    iris = store.iris_scores
    schools_df = store.schools

    residential = iris.dropna(subset=["population", "school_score"])

    # Population-weighted average schools per 1 000
    total_pop = residential["population"].sum()
    weighted_sum = (residential["schools_per_1000"] * residential["population"]).sum()
    avg_per_1000 = round(float(weighted_sum / total_pop), 4) if total_pop > 0 else 0.0

    # School-type breakdown from the silver catalog
    type_counts = (
        schools_df["type"]
        .value_counts()
        .reset_index()
        .rename(columns={"index": "type", "count": "count"})
    )
    school_types = [
        SchoolTypeCount(type=str(row["type"]), count=int(row["count"]))
        for _, row in type_counts.iterrows()
    ]

    return CityStats(
        total_iris_zones=len(iris),
        residential_iris_zones=len(residential),
        total_schools=len(schools_df),
        school_types=school_types,
        avg_schools_per_1000=avg_per_1000,
        avg_school_score=round(float(residential["school_score"].mean()), 4),
        max_school_score=round(float(residential["school_score"].max()), 4),
        min_school_score=round(float(residential["school_score"].min()), 4),
    )
