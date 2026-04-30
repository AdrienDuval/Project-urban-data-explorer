from pathlib import Path
import json
import pandas as pd
import numpy as np
import logging
import geopandas as gpd
from shapely.geometry import Point

from src.config import BDCOM_SILVER, GOLD, IRIS_GEOJSON
from src.db import engine

logger = logging.getLogger(__name__)


def export_to_gold(df: pd.DataFrame, name: str = 'bdcom') -> Path:
    """Export dataframe to gold layer CSV and return the path."""
    outdir = GOLD
    outdir.mkdir(parents=True, exist_ok=True)
    csv_path = outdir / f"{name}.csv"
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    logger.info(f"Exported {len(df)} records to {csv_path}")
    return csv_path


def _assign_code_iris_from_points(df: pd.DataFrame, x_col: str = 'X', y_col: str = 'Y') -> pd.Series:
    """Create a GeoSeries of code_iris by spatially joining point coordinates with IRIS polygons.

    Returns a pandas Series aligned with df index containing code_iris or None.
    """
    if x_col not in df.columns or y_col not in df.columns:
        return pd.Series([None] * len(df), index=df.index)

    # Load IRIS polygons and project to EPSG:2154
    iris = gpd.read_file(IRIS_GEOJSON)
    iris = iris[iris.get('dep', '') == '75'] if 'dep' in iris.columns else iris
    iris_proj = iris.to_crs(epsg=2154)

    # Build points from df coordinates
    pts = df[[x_col, y_col]].copy()
    pts[x_col] = pd.to_numeric(pts[x_col], errors='coerce')
    pts[y_col] = pd.to_numeric(pts[y_col], errors='coerce')

    # If coordinates appear to be lon/lat (< 180), set crs EPSG:4326 then reproject
    sample_x = pts[x_col].dropna().iloc[0] if pts[x_col].dropna().shape[0] > 0 else None
    use_lonlat = False
    if sample_x is not None and abs(sample_x) <= 180:
        use_lonlat = True

    if use_lonlat:
        gdf_pts = gpd.GeoDataFrame(pts, geometry=gpd.points_from_xy(pts[x_col], pts[y_col]), crs='EPSG:4326')
        gdf_pts = gdf_pts.to_crs(epsg=2154)
    else:
        gdf_pts = gpd.GeoDataFrame(pts, geometry=gpd.points_from_xy(pts[x_col], pts[y_col]), crs='EPSG:2154')

    # Spatial join
    joined = gpd.sjoin(gdf_pts, iris_proj[['code_iris', 'geometry']], how='left', predicate='within')
    code_series = joined['code_iris'] if 'code_iris' in joined.columns else pd.Series([None] * len(df), index=df.index)
    # Align to original index
    code_series.index = df.index
    return code_series


def process_bdcom_gold() -> pd.DataFrame:
    """
    Read BDCOM silver data, compute summary statistics, spatially assign code_iris, and export to gold.
    """
    logger.info(f"Loading BDCOM silver: {BDCOM_SILVER.name}")

    if not BDCOM_SILVER.exists():
        raise FileNotFoundError(f"BDCOM silver file not found: {BDCOM_SILVER}")

    df = pd.read_csv(BDCOM_SILVER)
    logger.info(f"Loaded {len(df):,} records from silver")

    # Assign IRIS codes via spatial join if coordinates exist
    if {'X', 'Y'}.issubset(df.columns):
        try:
            df['code_iris'] = _assign_code_iris_from_points(df, x_col='X', y_col='Y')
            logger.info("Assigned code_iris for BDCOM via spatial join")
        except Exception as e:
            logger.warning("Failed to assign code_iris via spatial join: %s", e)
            df['code_iris'] = None
    else:
        df['code_iris'] = None

    # Ensure code_iris is string and zero-padded when possible
    if 'code_iris' in df.columns:
        df['code_iris'] = df['code_iris'].astype(str).replace({'None': None}).where(pd.notnull(df['code_iris']), None)
        try:
            df.loc[df['code_iris'].notnull(), 'code_iris'] = df.loc[df['code_iris'].notnull(), 'code_iris'].str.zfill(9)
        except Exception:
            pass

    # === Numeric cleaning ===
    numeric_cols = ['surf', 'X', 'Y', 'arro', 'qua']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            if df[col].isnull().any():
                df[col] = df[col].fillna(df[col].median())

    # === Categorical cleaning ===
    categorical_cols = [
        'type', 'typ_voie', 'lib_voie', 'sit', 'bio', 'ens',
        'Libellé activité (224 postes)', 'TYPE', 'Libellé TYPE (local)',
        'Libellé activité 47 postes', 'Libellé activité 18 postes',
        'Libellé activité 8 postes)', 'Libellé activité 2 postes',
    ]
    for col in categorical_cols:
        if col in df.columns and df[col].isnull().any():
            mode_val = df[col].mode()
            if len(mode_val) > 0:
                df[col] = df[col].fillna(mode_val[0])

    # === Derived columns ===
    if 'Libellé activité (224 postes)' in df.columns:
        df['activite_label'] = df['Libellé activité (224 postes)']

    # Code columns as integers
    for code_col in ['niv47', 'niv18', 'niv8', 'niv2', 'codact']:
        if code_col in df.columns:
            df[code_col] = pd.to_numeric(df[code_col], errors='coerce').astype('Int64')

    # Boolean flags
    if 'bio' in df.columns:
        df['is_bio'] = df['bio'].astype(str).str.strip().isin(['1', 'Y', 'Yes', 'True', 'O'])

    if 'ens' in df.columns:
        df['in_ensemble'] = df['ens'].astype(str).str.strip().ne('0') & df['ens'].notna()

    # === Summary statistics ===
    logger.info(f"Shape: {df.shape}")
    missing = df.isnull().sum()
    if missing.any():
        logger.info(f"Missing values:\n{missing[missing > 0]}")

    logger.info(f"Numeric summary:\n{df[numeric_cols].describe().round(2)}")

    if 'Libellé activité (224 postes)' in df.columns:
        logger.info(f"Top activity types:\n{df['Libellé activité (224 postes)'].value_counts().head(10)}")

    if 'arro' in df.columns:
        logger.info(f"Commerce count by arrondissement:\n{df['arro'].value_counts().sort_index().head(20)}")

    if 'niv2' in df.columns and 'Libellé activité 2 postes' in df.columns:
        logger.info(f"Distribution by sector (niv2):\n{df.groupby(['niv2', 'Libellé activité 2 postes']).size().reset_index(name='count').sort_values('count', ascending=False).head(20)}")

    if 'surf' in df.columns and 'TYPE' in df.columns:
        logger.info(f"Surface stats by type:\n{df.groupby('TYPE')['surf'].describe().round(2)}")

    # Export to gold CSV
    export_to_gold(df, name='bdcom')

    # Export to MySQL
    df_sql = df.copy()
    for col in df_sql.columns:
        if df_sql[col].apply(lambda x: isinstance(x, (dict, list))).any():
            df_sql[col] = df_sql[col].apply(lambda x: json.dumps(x) if isinstance(x, (dict, list)) else x)
    df_sql.to_sql("bdcom", engine, if_exists="replace", index=False)
    logger.info("Inserted %d rows into MySQL table 'bdcom'", len(df_sql))

    return df


if __name__ == "__main__":
    try:
        path = Path("data/silver/bdcom.parquet")
        df = pd.read_parquet(path)
    except Exception:
        path = Path("data/silver/bdcom_paris_clean.csv")
        df = pd.read_csv(path)

    df_out = process_bdcom_gold()
    print(df_out.shape)
    print(df_out.head())