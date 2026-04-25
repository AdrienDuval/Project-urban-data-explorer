from __future__ import annotations
from pydantic import BaseModel, Field

class TransportIndicator(BaseModel):
    code_iris: str = Field(description="9-digit INSEE IRIS code.")
    x_sum_weights: float = Field(description="Somme des poids des points de transport dans le rayon.")
    density_score: float = Field(description="Score de densité normalisé (0-1).")
    proximity_score: float = Field(description="Score de proximité normalisé (0-1).")
    transport_score: float = Field(description="Score transport final (0-1).")

class TransportPoint(BaseModel):
    id: str = Field(description="Identifiant unique du point de transport.")
    name: str = Field(description="Nom de l'arrêt ou de la station.")
    type: str = Field(description="Type de transport (metro, bus, tram, rail, velib).")
    lat: float = Field(description="Latitude.")
    lng: float = Field(description="Longitude.")