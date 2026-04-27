from __future__ import annotations
from typing import Optional
import pandas as pd
from api.models.common import PaginatedResponse
from api.models.indicators.transport import TransportIndicator, TransportPoint
from api.services.data_loader import DataStore


def _row_to_indicator(row: pd.Series) -> TransportIndicator:
    return TransportIndicator(
        code_iris=str(row["CODE_IRIS"]).zfill(9),
        x_sum_weights=float(row["x_sum_weights"]),
        density_score=float(row["density_score"]),
        proximity_score=float(row["proximity_score"]),
        transport_score=float(row["transport_score"]),
    )


def _row_to_point(row: pd.Series) -> TransportPoint:
    return TransportPoint(
        id=str(row["id"]),
        name=str(row["name"]),
        type=str(row["type"]),
        lat=float(row["lat"]),
        lng=float(row["lng"]),
    )


def list_transport_indicators(
    store: DataStore,
    *,
    min_score: Optional[float] = None,
    max_score: Optional[float] = None,
    page: int = 1,
    size: int = 50,
) -> PaginatedResponse[TransportIndicator]:
    df = store.transport_scores.copy()
    if min_score is not None:
        df = df[df["transport_score"] >= min_score]
    if max_score is not None:
        df = df[df["transport_score"] <= max_score]
    total = len(df)
    page_df = df.iloc[(page - 1) * size : page * size]
    pages = max(1, -(-total // size))
    return PaginatedResponse(
        items=[_row_to_indicator(row) for _, row in page_df.iterrows()],
        total=total, page=page, size=size, pages=pages,
    )


def get_transport_indicator(
    store: DataStore, code_iris: str
) -> Optional[TransportIndicator]:
    code_iris = code_iris.zfill(9)
    matches = store.transport_scores[store.transport_scores["CODE_IRIS"] == code_iris]
    if matches.empty:
        return None
    return _row_to_indicator(matches.iloc[0])


def list_transport_points(
    store: DataStore,
    *,
    type_filter: Optional[str] = None,
) -> list[TransportPoint]:
    df = store.transport_points.copy()
    if type_filter:
        df = df[df["type"] == type_filter.lower()]
    return [_row_to_point(row) for _, row in df.iterrows()]