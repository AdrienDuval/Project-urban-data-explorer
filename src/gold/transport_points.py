"""
Silver → Gold: Transport Points

Fusionne les arrêts de transport public et les stations Vélib silver
en une table de référence géolocalisée pour la visualisation cartographique.

Sortie :
- data/gold/transport_points.csv
- DB table : transport_points
"""

import pandas as pd

from src.config import (
    TRANSPORT_ARRETS_SILVER,
    TRANSPORT_VELIB_SILVER,
    TRANSPORT_POINTS_GOLD,
)
from src.db import engine


def compute_transport_points() -> pd.DataFrame:
    """
    Charge et fusionne les silvers transport en une table Gold de référence.
    Colonnes de sortie : id, name, type, lat, lng
    """
    arrets = pd.read_csv(TRANSPORT_ARRETS_SILVER, encoding="utf-8")
    velib = pd.read_csv(TRANSPORT_VELIB_SILVER, encoding="utf-8")

    arrets = arrets[["id", "name", "type", "lat", "lng"]].copy()
    velib = velib[["id", "name", "type", "lat", "lng"]].copy()

    df = pd.concat([arrets, velib], ignore_index=True)

    # Nettoyage
    df["type"] = df["type"].astype(str).str.strip().str.lower()
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
    df["lng"] = pd.to_numeric(df["lng"], errors="coerce")
    df = df.dropna(subset=["lat", "lng"]).copy()
    df = df.drop_duplicates(subset=["id"]).copy()

    # Export
    TRANSPORT_POINTS_GOLD.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(TRANSPORT_POINTS_GOLD, index=False, encoding="utf-8-sig")
    df.to_sql("transport_points", engine, if_exists="replace", index=False)

    print(f"[transport_points] {len(df)} rows saved → {TRANSPORT_POINTS_GOLD}")
    print(df["type"].value_counts().to_dict())

    return df


if __name__ == "__main__":
    compute_transport_points()