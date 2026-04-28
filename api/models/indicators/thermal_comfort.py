from pydantic import BaseModel
from typing import Optional

class ThermalComfortIndicator(BaseModel):
    code_iris: str
    nom_iris: str
    arrondissement: str
    nb_arbres: int
    nb_ilots: int
    thermal_comfort_score: float
    thermal_comfort_rank: Optional[int] = None

class ThermalComfortArrondissementStats(BaseModel):
    arrondissement: str
    avg_score: float
    total_arbres: int
    count_iris: int