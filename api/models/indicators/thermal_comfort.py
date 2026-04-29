from pydantic import BaseModel
from typing import Optional


class ThermalComfortIndicator(BaseModel):
    code_iris: str
    nom_iris: str
    arrondissement: str
    densite_arbres: Optional[float] = None
    ratio_fraicheur: Optional[float] = None
    tree_density_score: Optional[float] = None
    cooling_area_score: Optional[float] = None
    thermal_score: Optional[float] = None


class ThermalComfortFeatureProperties(BaseModel):
    """Propriétés GeoJSON — noms attendus par le frontend."""
    code_iris: str
    name: str                        # = nom_iris
    arrondissement: str
    geography: str = "iris"
    densite_arbres: Optional[float] = None
    tree_density_score: Optional[float] = None
    cooling_area_score: Optional[float] = None
    thermal_score: Optional[float] = None


class ThermalComfortArrondissementStats(BaseModel):
    arrondissement: str
    avg_score: float
    count_iris: int