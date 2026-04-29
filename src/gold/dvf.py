from sklearn.pipeline import Pipeline
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import MinMaxScaler, OneHotEncoder  # ← MinMaxScaler
import numpy as np
import pandas as pd
from pathlib import Path


def export_to_gold(df: pd.DataFrame, name: str = 'dvf') -> None:
    outdir = Path('data/gold')
    outdir.mkdir(parents=True, exist_ok=True)
    csv_path = outdir / f"{name}.csv"
    df.to_csv(csv_path, index=False)
    print(f"\nExported to {csv_path}")


def build_dvf_pipeline(
    df: pd.DataFrame,
    numeric_cols=None,
    categorical_cols=None,
):
    if numeric_cols is None:
        numeric_cols = ['surface_m2', 'prix_m2', 'valeur_fonciere', 'annee', 'mois']
    if categorical_cols is None:
        categorical_cols = ['arrondissement', 'type_local']

    # --- clean numeric columns: impute missing with median, keep original scale ---
    for col in numeric_cols:
        if col in df.columns:
            median_val = df[col].median()
            df[col] = df[col].fillna(median_val)

    # --- clean categorical columns: impute missing with most frequent ---
    for col in categorical_cols:
        if col in df.columns:
            most_frequent = df[col].mode()[0]
            df[col] = df[col].fillna(most_frequent)

    # --- derived columns: useful aggregations ---
    if 'valeur_fonciere' in df.columns and 'surface_m2' in df.columns:
        df['prix_m2'] = (df['valeur_fonciere'] / df['surface_m2']).round(2)

    if 'annee' in df.columns and 'mois' in df.columns:
        df['date'] = pd.to_datetime(
            df['annee'].astype(str) + '-' + df['mois'].astype(str).str.zfill(2),
            format='%Y-%m', errors='coerce'
        )

    # --- summary stats printed for quick insight ---
    print("=== Shape ===")
    print(df.shape)

    print("\n=== Missing values ===")
    missing = df.isnull().sum()
    print(missing[missing > 0] if missing.any() else "None")

    print("\n=== Numeric summary ===")
    print(df[numeric_cols].describe().round(2))

    print("\n=== Top arrondissements by avg prix_m2 ===")
    if 'arrondissement' in df.columns and 'prix_m2' in df.columns:
        print(
            df.groupby('arrondissement')['prix_m2']
            .mean().round(2)
            .sort_values(ascending=False)
            .head(10)
        )

    print("\n=== Transaction count by type_local ===")
    if 'type_local' in df.columns:
        print(df['type_local'].value_counts())

    export_to_gold(df, name='dvf')
    return df

if __name__ == "__main__":
    try:
        dvf_silver_path = Path("data/silver/dvf.parquet")
        df = pd.read_parquet(dvf_silver_path)
    except Exception:
        dvf_silver_path = Path("data/silver/dvf_paris_clean.csv")
        df = pd.read_csv(dvf_silver_path)


    df_out = build_dvf_pipeline(df)
    print(df_out.shape)
    print(df_out.head())