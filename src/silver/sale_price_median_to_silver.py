import os

import pdfplumber
import pandas as pd

from src.config import SALE_PRICE_SILVER, SALE_PRICE_PDF


def process_sale_price_median_to_silver():
    # Chargement des données au format pdf
    pdf_path = SALE_PRICE_PDF

    # on extrait les tables des 3 pages du pdf
    with pdfplumber.open(pdf_path) as pdf:
        table1 = pdf.pages[0].extract_table()
        table2 = pdf.pages[1].extract_table()
        table3 = pdf.pages[2].extract_table()

    # Conversion en DataFrames Pandas
    df1 = pd.DataFrame(table1[1:], columns=table1[0])
    df2 = pd.DataFrame(table2[1:], columns=table2[0])
    df3 = pd.DataFrame(table3[1:], columns=table3[0])

    # Concaténation
    df = pd.concat([df1, df2, df3], axis=0, ignore_index=True)

    # Suppression des symboles € et les espaces insécables
    for col in df.columns:
        if col != "Trimestre":
            df[col] = df[col].str.replace(r"[€\s\n]", "", regex=True)

    # Suppression de la colonne "Centre"
    if "Centre" in df.columns:
        df = df.drop(columns=["Centre"])

    # on récupère les colonnes d'arrondissement
    col_ardt = [col for col in df.columns if col != "Trimestre"]
    df_long = df.melt(
        id_vars=["Trimestre"], 
        value_vars=col_ardt,
        var_name="arrondissement", 
        value_name="prix_m2"
    )

    # 5. Nettoyage arrondissement (extraire le nombre) et prix (convertir en float)
    df_long["arrondissement"] = df_long["arrondissement"].str.extract(r"(\d+)").astype(int)
    df_long["prix_m2"] = pd.to_numeric(df_long["prix_m2"], errors='coerce')


    # 6. Transformation du Trimestre en Date
    # On s'assure de ne garder que les lignes qui contiennent un tiret "-"
    df_long = df_long[df_long["Trimestre"].notnull()].copy()

    # On split proprement
    split_trim = df_long["Trimestre"].str.split(" ", expand=True)

    # On vérifie si on a bien récupéré 2 colonnes
    if split_trim.shape[1] == 2:
        annee = split_trim[1]
        trimestre = split_trim[0]

        # Mapping des trimestres vers le premier jour du trimestre
        mapping_mois = {"T1": "01-01", "T2": "04-01", "T3": "07-01", "T4": "10-01"}
        mois_jour = trimestre.str.strip().map(mapping_mois) # .str.strip() au cas où il y a un espace

        # Création de la colonne date
        df_long["date_periode"] = pd.to_datetime(annee + "-" + mois_jour)
    else:
        print("Erreur : Le format des trimestres est inattendu.")
        print(split_trim.head())


    output_dir = os.path.dirname(SALE_PRICE_SILVER)
    os.makedirs(output_dir, exist_ok=True)
    df_long.to_csv(SALE_PRICE_SILVER, sep=";", index=False, encoding="utf-8")

if __name__ == "__main__":
    process_sale_price_median_to_silver()