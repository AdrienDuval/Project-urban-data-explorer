import io
import json
import logging
from pathlib import Path

import geopandas as gpd
import pandas as pd

from src.config import DVF_SILVER, GOLD, IRIS_GEOJSON
from src.db import engine

logger = logging.getLogger(__name__)

_BAN_URL = 'https://api-adresse.data.gouv.fr/search/csv/'
_BATCH_SIZE = 10_000


def export_to_gold(df: pd.DataFrame, name: str = 'dvf') -> Path:
    """Export dataframe to gold layer CSV and return the path."""
    outdir = GOLD
    outdir.mkdir(parents=True, exist_ok=True)
    csv_path = outdir / f"{name}.csv"
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    logger.info(f"Exported {len(df)} records to {csv_path}")
    return csv_path


def _geocode_via_ban(df: pd.DataFrame) -> tuple[pd.Series, pd.Series]:
    """Batch-geocode DVF addresses using the BAN CSV API. Returns (lat, lon) Series."""
    import httpx

    lat_all = pd.Series([None] * len(df), dtype=object, index=df.index)
    lon_all = pd.Series([None] * len(df), dtype=object, index=df.index)

    for i in range(0, len(df), _BATCH_SIZE):
        batch = df.iloc[i:i + _BATCH_SIZE]
        addr = (
            batch.get('numero_voie', pd.Series(dtype=str)).fillna('').astype(str).str.strip()
            + ' '
            + batch.get('type_voie', pd.Series(dtype=str)).fillna('').astype(str).str.strip()
            + ' '
            + batch.get('nom_voie', pd.Series(dtype=str)).fillna('').astype(str).str.strip()
        ).str.strip()
        postcode = batch.get('code_postal', pd.Series(dtype=str)).fillna('').astype(str).str.strip()

        inp_csv = pd.DataFrame({'q': addr.values, 'postcode': postcode.values}).to_csv(index=False).encode('utf-8')
        try:
            with httpx.Client(timeout=180) as client:
                resp = client.post(
                    _BAN_URL,
                    files={'data': ('addr.csv', inp_csv, 'text/csv')},
                    data={'columns[]': 'q', 'postcode': 'postcode'},
                )
                resp.raise_for_status()
            result = pd.read_csv(io.BytesIO(resp.content))
            lat_all.iloc[i:i + len(batch)] = pd.to_numeric(
                result.get('latitude', pd.Series(dtype='float64')), errors='coerce'
            ).values
            lon_all.iloc[i:i + len(batch)] = pd.to_numeric(
                result.get('longitude', pd.Series(dtype='float64')), errors='coerce'
            ).values
            logger.info(f"Geocoded rows {i}–{i + len(batch) - 1}")
        except Exception as e:
            logger.warning(f"BAN geocoding failed for rows {i}–{i + len(batch) - 1}: {e}")

    return lat_all, lon_all


def _spatial_join_iris(lat: pd.Series, lon: pd.Series, index: pd.Index) -> pd.Series:
    """Point-in-polygon join of (lat, lon) coordinates with Paris IRIS polygons."""
    code_iris = pd.Series([None] * len(index), index=index)

    lat_num = pd.to_numeric(lat, errors='coerce')
    lon_num = pd.to_numeric(lon, errors='coerce')
    valid = lat_num.notna() & lon_num.notna()

    if not valid.any():
        logger.warning("No geocoded coordinates available — code_iris will be null")
        return code_iris

    iris = gpd.read_file(IRIS_GEOJSON)
    if 'dep' in iris.columns:
        iris = iris[iris['dep'] == '75']
    iris_proj = iris.to_crs(epsg=2154)

    gdf_pts = gpd.GeoDataFrame(
        index=index[valid],
        geometry=gpd.points_from_xy(lon_num[valid].values, lat_num[valid].values),
        crs='EPSG:4326',
    ).to_crs(epsg=2154)

    joined = gpd.sjoin(gdf_pts, iris_proj[['code_iris', 'geometry']], how='left', predicate='within')
    code_iris[joined.index] = joined['code_iris'].values
    return code_iris


def _assign_code_iris(df: pd.DataFrame) -> pd.Series:
    """Assign code_iris to DVF records.

    Uses stored lat/lon if present in the silver data; otherwise geocodes via
    the BAN batch API and falls back to all-null if the API is unreachable.
    """
    # Fast path: silver already has coordinates (e.g., from a future raw source)
    if 'latitude' in df.columns and 'longitude' in df.columns and df['latitude'].notna().any():
        logger.info("Using stored latitude/longitude for IRIS spatial join")
        lat = pd.to_numeric(df['latitude'], errors='coerce')
        lon = pd.to_numeric(df['longitude'], errors='coerce')
        return _spatial_join_iris(lat, lon, df.index)

    # Geocode via BAN API
    logger.info(f"Geocoding {len(df):,} DVF addresses via BAN API (batches of {_BATCH_SIZE:,})")
    lat, lon = _geocode_via_ban(df)
    return _spatial_join_iris(lat, lon, df.index)


def process_dvf_gold() -> pd.DataFrame:
    """
    Read DVF silver data, compute aggregated statistics, and export to gold.

    This creates summary views of housing transactions in Paris
    suitable for dashboard display (price trends, volume by arrondissement, etc.).
    """
    logger.info(f"Loading DVF silver: {DVF_SILVER.name}")

    if not DVF_SILVER.exists():
        raise FileNotFoundError(f"DVF silver file not found: {DVF_SILVER}")

    df = pd.read_csv(DVF_SILVER)
    logger.info(f"Loaded {len(df):,} transactions from silver")

    # === Assign IRIS code ===
    try:
        df['code_iris'] = _assign_code_iris(df)
        df['code_iris'] = (
            df['code_iris']
            .astype(str)
            .replace({'None': None, 'nan': None})
            .where(pd.notnull(df['code_iris']), None)
        )
        df.loc[df['code_iris'].notnull(), 'code_iris'] = (
            df.loc[df['code_iris'].notnull(), 'code_iris'].str.zfill(9)
        )
        pct = df['code_iris'].notna().mean() * 100
        logger.info(f"code_iris assigned: {pct:.1f}% of rows")
    except Exception as e:
        logger.warning("Failed to assign code_iris: %s", e)
        df['code_iris'] = None

    # === Numeric cleaning ===
    numeric_cols = ['surface_m2', 'prix_m2', 'valeur_fonciere', 'annee', 'mois', 'nb_pieces']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            if df[col].isnull().any():
                median_val = df[col].median()
                if pd.notna(median_val):
                    df[col] = df[col].fillna(median_val)

    # === Categorical cleaning ===
    categorical_cols = ['arrondissement', 'type_local', 'nature_culture', 'nature_mutation']
    for col in categorical_cols:
        if col in df.columns and df[col].isnull().any():
            mode_val = df[col].mode()
            if len(mode_val) > 0:
                df[col] = df[col].fillna(mode_val[0])

    # === Derived columns ===
    if 'valeur_fonciere' in df.columns and 'surface_m2' in df.columns:
        df['prix_m2'] = (df['valeur_fonciere'] / df['surface_m2']).round(2)

    if 'annee' in df.columns and 'mois' in df.columns:
        df['date'] = pd.to_datetime(
            df['annee'].astype(str) + '-' + df['mois'].astype(str).str.zfill(2),
            format='%Y-%m', errors='coerce'
        )

    # === Summary statistics ===
    logger.info(f"Shape: {df.shape}")
    missing = df.isnull().sum()
    if missing.any():
        logger.info(f"Missing values:\n{missing[missing > 0]}")

    logger.info(f"Numeric summary:\n{df[numeric_cols].describe().round(2)}")

    if 'arrondissement' in df.columns and 'prix_m2' in df.columns:
        logger.info(f"Top arrondissements by avg prix_m2:\n{df.groupby('arrondissement')['prix_m2'].mean().round(2).sort_values(ascending=False).head(10)}")

    if 'type_local' in df.columns:
        logger.info(f"Transaction count by type_local:\n{df['type_local'].value_counts()}")

    if 'annee' in df.columns:
        logger.info(f"Transaction count by year:\n{df['annee'].value_counts().sort_index()}")

    if 'prix_m2' in df.columns:
        logger.info(f"Median prix_m2: {df['prix_m2'].median():,.0f} €")
        logger.info(f"Median surface_m2: {df['surface_m2'].median():,.0f} m²")

    # Export to gold CSV
    export_to_gold(df, name='dvf')

    # Export to MySQL
    df_sql = df.copy()
    for col in df_sql.columns:
        if df_sql[col].apply(lambda x: isinstance(x, (dict, list))).any():
            df_sql[col] = df_sql[col].apply(lambda x: json.dumps(x) if isinstance(x, (dict, list)) else x)
    df_sql.to_sql("dvf", engine, if_exists="replace", index=False)
    logger.info("Inserted %d rows into MySQL table 'dvf'", len(df_sql))

    return df


if __name__ == "__main__":
    try:
        dvf_silver_path = Path("data/silver/dvf.parquet")
        df = pd.read_parquet(dvf_silver_path)
    except Exception:
        dvf_silver_path = Path("data/silver/dvf_paris_clean.csv")
        df = pd.read_csv(dvf_silver_path)

    df_out = process_dvf_gold()
    print(df_out.shape)
    print(df_out.head())