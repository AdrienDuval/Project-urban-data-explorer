import pdfplumber
import polars as pl
import geopandas as gpd

# Chargement des données au format pdf
pdf_path = "./data/bronze/main_data/HistoriquedesprixaumappartementsanciensParispararrdt_2.pdf"

# on extrait les tables des 3 pages du pdf
with pdfplumber.open(pdf_path) as pdf:
    table1 = pdf.pages[0].extract_table()
    table2 = pdf.pages[1].extract_table()
    table3 = pdf.pages[2].extract_table()

# Conversion en DataFrames Polars
# On utilise Polars pour sa rapidité et son efficacité dans le traitement de données volumineuses.
# On utilise la première ligne comme noms de colonnes
df1 = pl.DataFrame(table1[1:], schema=table1[0])
df2 = pl.DataFrame(table2[1:], schema=table2[0])
df3 = pl.DataFrame(table3[1:], schema=table3[0])

# On concatène les trois DataFrames en un seul
df = pl.concat([df1, df2, df3], how="vertical")

# Suppression des symboles € et les espaces insécables
df = df.with_columns([
    pl.col(col).str.replace_all(r"[€\s\n]", "") for col in df.columns if col != "Trimestre"
])

# On supprime la colonne "Centre" qui ne correspond pas à un arrondissement
df.drop_in_place("Centre")

# on récupère les colonnes d'arrondissement
col_ardt = [col for col in df.columns if col != "Trimestre"]

# Opération de Dépivotage pour avoir les arrondissements et les prix en lignes
# on aura 1 ligne avec le trimestre, l'arrondissement et le prix au m2
df_long = df.unpivot(
    on=col_ardt,
    index=["Trimestre"],
    variable_name="arrondissement",
    value_name="prix_m2"
)

# convertir les arrondissement en int (en enlevant les caractères type "er", "ème", etc.)
df_long = df_long.with_columns(
    pl.col("arrondissement").str.extract(r"(\d+)", 1).cast(pl.Int64)
)

df_long.write_csv("./data/bronze/main_data/sale_price_m2.csv", separator=";")

##############################################################
### Lien avec geojson
##############################################################

gdf_arrdt = gpd.read_file("./data/bronze/main_data/arrondissements.geojson")

df_pandas = df_long.to_pandas()

# On fusionne les données de prix avec les données géographiques
gdf_merged = gdf_arrdt.merge(df_pandas, left_on="c_ar", right_on="arrondissement")

gdf_merged.to_file("./data/bronze/main_data/prix_immobilier_geospatial.geojson", driver='GeoJSON')