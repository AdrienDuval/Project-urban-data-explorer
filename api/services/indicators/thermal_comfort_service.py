from __future__ import annotations
from typing import List, Optional
import pandas as pd
from sqlalchemy import text
from api.dependencies import DataStore
from api.models.indicators.thermal_comfort import (
    ThermalComfortIndicator,
    ThermalComfortArrondissementStats,
)

def list_thermal_comfort_indicators(
    store: DataStore,
    arrondissement: Optional[str] = None,
    min_score: Optional[float] = None,
    limit: int = 20,
    offset: int = 0,
) -> dict:
    """Récupère les scores de confort thermique depuis MySQL."""
    query = "SELECT * FROM thermal_comfort WHERE 1=1"
    params = {}

    if arrondissement:
        query += " AND arrondissement LIKE :arrdt"
        params["arrdt"] = f"%{arrondissement}%"
    
    if min_score is not None:
        query += " AND thermal_comfort_score >= :min_score"
        params["min_score"] = min_score

    # On ajoute le tri par rang
    query += " ORDER BY thermal_comfort_score DESC LIMIT :limit OFFSET :offset"
    params["limit"] = limit
    params["offset"] = offset

    with store.engine.connect() as conn:
        df = pd.read_sql(text(query), conn, params=params)
        
    # Calcul du total pour la pagination
    total_query = "SELECT COUNT(*) FROM thermal_comfort"
    with store.engine.connect() as conn:
        total = conn.execute(text(total_query)).scalar()

    return {
        "items": df.to_dict(orient="records"),
        "total": total,
        "limit": limit,
        "offset": offset,
    }

def list_thermal_comfort_arrondissements(store: DataStore) -> List[ThermalComfortArrondissementStats]:
    """Agrège les données par arrondissement."""
    query = """
        SELECT 
            arrondissement, 
            AVG(thermal_comfort_score) as avg_score,
            SUM(nb_arbres) as total_arbres,
            COUNT(*) as count_iris
        FROM thermal_comfort 
        GROUP BY arrondissement
        ORDER BY arrondissement ASC
    """
    with store.engine.connect() as conn:
        df = pd.read_sql(text(query), conn)
    return df.to_dict(orient="records")

def get_thermal_comfort_indicator(store: DataStore, code_iris: str) -> Optional[ThermalComfortIndicator]:
    """Récupère un IRIS précis."""
    query = "SELECT * FROM thermal_comfort WHERE code_iris = :code"
    with store.engine.connect() as conn:
        df = pd.read_sql(text(query), conn, params={"code": code_iris})
    
    if df.empty:
        return None
    return df.iloc[0].to_dict()