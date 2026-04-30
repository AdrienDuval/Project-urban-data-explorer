import logging
from pathlib import Path

import pandas as pd

from src.config import DVF_SILVER, GOLD

logger = logging.getLogger(__name__)


def export_to_gold(df: pd.DataFrame, name: str = 'dvf') -> Path:
    """Export dataframe to gold layer CSV and return the path."""
    outdir = GOLD
    outdir.mkdir(parents=True, exist_ok=True)
    csv_path = outdir / f"{name}.csv"
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    logger.info(f"Exported {len(df)} records to {csv_path}")
    return csv_path


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

    # Export to gold
    export_to_gold(df, name='dvf')

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