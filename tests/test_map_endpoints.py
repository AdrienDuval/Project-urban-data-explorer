from types import SimpleNamespace

import geopandas as gpd
import pandas as pd
from fastapi import FastAPI
from fastapi.testclient import TestClient
from shapely.geometry import Polygon

from api.routers import map as map_router


def _square() -> Polygon:
    return Polygon([(2.0, 48.0), (2.1, 48.0), (2.1, 48.1), (2.0, 48.1)])


def _client(store: SimpleNamespace) -> TestClient:
    app = FastAPI()
    app.state.data = store
    app.include_router(map_router.router, prefix="/map")
    return TestClient(app)


def test_vivabilite_map_endpoint_returns_geojson():
    store = SimpleNamespace(
        iris_geojson={
            "type": "FeatureCollection",
            "features": [
                {
                    "type": "Feature",
                    "geometry": {
                        "type": "Polygon",
                        "coordinates": [
                            [
                                [2.0, 48.0],
                                [2.1, 48.0],
                                [2.1, 48.1],
                                [2.0, 48.1],
                                [2.0, 48.0],
                            ]
                        ],
                    },
                    "properties": {"code_iris": "751010101", "nom_iris": "Demo"},
                }
            ],
        },
        vivabilite_scores=pd.DataFrame(
            [
                {
                    "IRIS": "751010101",
                    "LIBIRIS": "Demo IRIS",
                    "LIBCOM": "Paris 1er Arrondissement",
                    "essential_connectivity_score": 8.1,
                    "essential_connectivity_rank": 1,
                    "vivabilite_score": 7.2,
                    "vivabilite_rank": 1,
                }
            ]
        ),
    )

    response = _client(store).get("/map/vivabilite-familiale")

    assert response.status_code == 200
    payload = response.json()
    assert payload["type"] == "FeatureCollection"
    assert payload["features"][0]["properties"]["vivabilite_score"] == 7.2
    assert payload["features"][0]["properties"]["essential_connectivity_score"] == 8.1


def test_thermal_comfort_map_endpoint_returns_geojson():
    store = SimpleNamespace(
        thermal_comfort_scores=gpd.GeoDataFrame(
            [
                {
                    "code_iris": "751010101",
                    "nom_iris": "Demo IRIS",
                    "densite_arbres": 25.0,
                    "ratio_fraicheur": 0.2,
                    "indice_confort_thermique": 62.0,
                }
            ],
            geometry=[_square()],
            crs="EPSG:4326",
        )
    )

    response = _client(store).get("/map/thermal-comfort")

    assert response.status_code == 200
    assert response.json()["features"][0]["properties"]["thermal_score"] == 6.2


def test_rent_map_endpoint_returns_geojson():
    store = SimpleNamespace(
        rent_price_scores=gpd.GeoDataFrame(
            [
                {
                    "c_ar": "1",
                    "l_aroff": "Louvre",
                    "l_ar": "1er Ardt",
                    "loyer_median_m2": 30.0,
                    "loyer_q1_m2": 26.0,
                    "loyer_q3_m2": 34.0,
                }
            ],
            geometry=[_square()],
            crs="EPSG:4326",
        )
    )

    response = _client(store).get("/map/housing/rent")

    assert response.status_code == 200
    assert response.json()["features"][0]["properties"]["loyer_median_m2"] == 30.0


def test_sale_map_endpoint_returns_latest_geojson():
    store = SimpleNamespace(
        sale_price_scores=gpd.GeoDataFrame(
            [
                {
                    "c_ar": "1",
                    "l_aroff": "Louvre",
                    "l_ar": "1er Ardt",
                    "prix_m2": 10_000,
                    "Trimestre": "T1 2025",
                    "date_periode": "2025-01-01",
                },
                {
                    "c_ar": "1",
                    "l_aroff": "Louvre",
                    "l_ar": "1er Ardt",
                    "prix_m2": 12_000,
                    "Trimestre": "T4 2025",
                    "date_periode": "2025-10-01",
                },
            ],
            geometry=[_square(), _square()],
            crs="EPSG:4326",
        )
    )

    response = _client(store).get("/map/housing/sale")

    assert response.status_code == 200
    props = response.json()["features"][0]["properties"]
    assert props["prix_m2"] == 12_000
    assert props["date_periode"] == "2025-10-01"
