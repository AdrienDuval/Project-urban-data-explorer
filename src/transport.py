"""
Bronze → Silver: Transport

Nettoie :
- les arrêts de transport public depuis arrets.csv
- les stations Vélib depuis velib.csv

Sorties :
- data/silver/transport_arrets_paris.csv
- data/silver/velib_paris.csv
"""

import pandas as pd

from src.config import (
    TRANSPORT_ARRETS_RAW,
    TRANSPORT_VELIB_RAW,
    TRANSPORT_ARRETS_SILVER,
    TRANSPORT_VELIB_SILVER,
)


# -------------------------------------------------------------------------
# Helpers
# -------------------------------------------------------------------------
def _read_csv_auto(path) -> pd.DataFrame:
    """Lecture CSV avec détection automatique du séparateur."""
    return pd.read_csv(path, sep=";")


def _split_geopoint(series: pd.Series) -> pd.DataFrame:
    """
    Transforme une colonne texte 'lat,lon' en deux colonnes numériques lat/lng.
    """
    coords = (
        series.astype(str)
        .str.replace(" ", "", regex=False)
        .str.split(",", n=1, expand=True)
    )

    if coords.shape[1] != 2:
        return pd.DataFrame({"lat": pd.Series(dtype=float), "lng": pd.Series(dtype=float)})

    return pd.DataFrame({
        "lat": pd.to_numeric(coords[0], errors="coerce"),
        "lng": pd.to_numeric(coords[1], errors="coerce"),
    })


# -------------------------------------------------------------------------
# Arrêts de transport public
# -------------------------------------------------------------------------
def process_transport_arrets() -> pd.DataFrame:
    """
    Nettoie les arrêts de transport public.

    Colonnes de sortie :
        id, name, type, lat, lng, town, postal_region
    """
    df = _read_csv_auto(TRANSPORT_ARRETS_RAW)

    # Harmonisation minimale
    df = df.rename(columns={
        "ArRId": "id",
        "ArRName": "name",
        "ArRType": "type",
        "ArRTown": "town",
        "ArRPostalRegion": "postal_region",
        "ArRGeopoint": "geopoint",
    })

    # Extraction coordonnées
    coords = _split_geopoint(df["geopoint"])
    df["lat"] = coords["lat"]
    df["lng"] = coords["lng"]

    # Normalisation type
    df["type"] = df["type"].astype(str).str.strip().str.lower()

    df["postal_region"] = df["postal_region"].astype(str).str.strip()
    
    # Filtre Paris uniquement via code postal/région
    before = len(df)
    df = df[df["postal_region"].str.startswith("75", na=False)]
    print(f"[transport_arrets] Paris postal filter kept {len(df)}/{before} rows")

    # Nettoyage de base
    df["id"] = df["id"].astype(str).str.strip()
    df["name"] = df["name"].astype(str).str.strip()

    # Suppression doublons
    df = df.drop_duplicates(subset=["id"], keep="first")

    # Schéma final
    df = df[["id", "name", "type", "lat", "lng", "town", "postal_region"]].copy()

    TRANSPORT_ARRETS_SILVER.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(TRANSPORT_ARRETS_SILVER, index=False)

    print(f"[transport_arrets] {len(df)} rows saved → {TRANSPORT_ARRETS_SILVER.name}")
    print(f"  Breakdown: {df['type'].value_counts().to_dict()}")
    return df


# -------------------------------------------------------------------------
# Vélib
# -------------------------------------------------------------------------
def process_velib() -> pd.DataFrame:
    """
    Nettoie les stations Vélib.

    Colonnes de sortie :
        id, name, type, lat, lng, code_insee
    """
    df = _read_csv_auto(TRANSPORT_VELIB_RAW)

    df = df.rename(columns={
    "Identifiant station": "id",
    "Nom station": "name",
    "Capacité de la station": "capacity",
    "Coordonnées géographiques": "geopoint",
    "Code INSEE communes équipées": "code_insee",
    "Nom communes équipées": "commune",
})

    # Extraction coordonnées
    coords = _split_geopoint(df["geopoint"])
    df["lat"] = coords["lat"]
    df["lng"] = coords["lng"]

    df["capacity"] = pd.to_numeric(df["capacity"], errors="coerce")
    df = df[df["capacity"] > 0]
    
    # Type fixé
    df["type"] = "velib"
    df["code_insee"] = df["code_insee"].astype(str).str.strip()
    df["commune"] = df["commune"].astype(str).str.strip()
    # Filtre Paris uniquement via code INSEE
    before = len(df)
    df = df[df["code_insee"].str.startswith("75", na=False)]
    print(f"[velib] Paris INSEE filter kept {len(df)}/{before} rows")

    # Nettoyage de base
    df["id"] = df["id"].astype(str).str.strip()
    df["name"] = df["name"].astype(str).str.strip()

    # Suppression doublons
    df = df.drop_duplicates(subset=["id"], keep="first")

    # Schéma final
    df = df[["id", "name", "type", "lat", "lng", "capacity", "code_insee", "commune"]].copy()

    TRANSPORT_VELIB_SILVER.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(TRANSPORT_VELIB_SILVER, index=False)

    print(f"[velib] {len(df)} rows saved → {TRANSPORT_VELIB_SILVER.name}")
    return df


# -------------------------------------------------------------------------
# Main
# -------------------------------------------------------------------------
def process_transport():
    """
    Lance les deux traitements silver transport.
    """
    arrets_df = process_transport_arrets()
    velib_df = process_velib()
    return arrets_df, velib_df


if __name__ == "__main__":
    process_transport()