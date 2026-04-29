from pathlib import Path
import pandas as pd
import numpy as np


def export_to_gold(df: pd.DataFrame, name: str = 'bdcom') -> None:
    outdir = Path('data/gold')
    outdir.mkdir(parents=True, exist_ok=True)
    csv_path = outdir / f"{name}.csv"
    df.to_csv(csv_path, index=False)
    print(f"\nExported to {csv_path}")


def build_bdcom_pipeline(
    df: pd.DataFrame,
    numeric_cols=None,
    categorical_cols=None,
):
    if numeric_cols is None:
        numeric_cols = ['surf', 'X', 'Y', 'arro', 'qua']
    if categorical_cols is None:
        categorical_cols = [
            'type', 'typ_voie', 'lib_voie', 'sit',
            'bio', 'ens',
            'Libellé activité (224 postes)',
            'TYPE', 'Libellé TYPE (local)',
            'Libellé activité 47 postes',
            'Libellé activité 18 postes',
            'Libellé activité 8 postes)',   # note: matches the typo in the header
            'Libellé activité 2 postes',
        ]

    # --- clean numeric columns: impute missing with median, keep original scale ---
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')
            df[col] = df[col].fillna(df[col].median())

    # --- clean categorical columns: impute missing with most frequent ---
    for col in categorical_cols:
        if col in df.columns:
            df[col] = df[col].fillna(df[col].mode()[0])

    # --- derived columns ---
    # activity hierarchy label (most detailed available)
    if 'Libellé activité (224 postes)' in df.columns:
        df['activite_label'] = df['Libellé activité (224 postes)']

    # keep only the code columns as clean ints
    for code_col in ['niv47', 'niv18', 'niv8', 'niv2', 'codact']:
        if code_col in df.columns:
            df[code_col] = pd.to_numeric(df[code_col], errors='coerce').astype('Int64')

    # bio as boolean flag
    if 'bio' in df.columns:
        df['is_bio'] = df['bio'].astype(str).str.strip().isin(['1', 'Y', 'Yes', 'True', 'O'])

    # ensemble commercial flag
    if 'ens' in df.columns:
        df['in_ensemble'] = df['ens'].astype(str).str.strip().ne('0') & df['ens'].notna()

    # --- summary stats ---
    print("=== Shape ===")
    print(df.shape)

    print("\n=== Missing values ===")
    missing = df.isnull().sum()
    print(missing[missing > 0] if missing.any() else "None")

    print("\n=== Numeric summary ===")
    existing_numeric = [c for c in numeric_cols if c in df.columns]
    print(df[existing_numeric].describe().round(2))

    print("\n=== Top activity types (224 postes) ===")
    if 'Libellé activité (224 postes)' in df.columns:
        print(df['Libellé activité (224 postes)'].value_counts().head(10))

    print("\n=== Commerce count by arrondissement ===")
    if 'arro' in df.columns:
        print(df['arro'].value_counts().sort_index().head(20))

    print("\n=== Distribution by niv2 (broad sector) ===")
    if 'niv2' in df.columns and 'Libellé activité 2 postes' in df.columns:
        print(
            df.groupby(['niv2', 'Libellé activité 2 postes'])
            .size()
            .reset_index(name='count')
            .sort_values('count', ascending=False)
        )

    print("\n=== Surface stats by type ===")
    if 'surf' in df.columns and 'TYPE' in df.columns:
        print(
            df.groupby('TYPE')['surf']
            .describe().round(2)
        )

    export_to_gold(df, name='bdcom')
    return df


if __name__ == "__main__":
    try:
        path = Path("data/silver/bdcom.parquet")
        df = pd.read_parquet(path)
    except Exception:
        path = Path("data/silver/bdcom_paris_clean.csv")
        df = pd.read_csv(path)

    df_out = build_bdcom_pipeline(df)
    print(df_out.shape)
    print(df_out.head())