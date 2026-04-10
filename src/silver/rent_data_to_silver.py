
import geopandas as gpd
import polars as pl

# 1. Charger les quartiers depuis le KML (Source Bronze)
# Note: 'fiona' est nécessaire pour lire le KML
# gpd.io.file_io.pyogrio_drivers['KML'] = 'rw'
df_quartiers_geo = gpd.read_file("./data/bronze/rent_data/L7501_zone_elem_2024.kml", driver='KML')

# 2. Charger tes arrondissements (ton GeoJSON actuel)
df_arrondissements_geo = gpd.read_file("./data/bronze/main_data/arrondissements.geojson")

df_quartiers_geo = df_quartiers_geo.to_crs(epsg=4326)
df_arrondissements_geo = df_arrondissements_geo.to_crs(epsg=4326)

quartiers_points = df_quartiers_geo.copy()
quartiers_points['geometry'] = quartiers_points.geometry.representative_point()

# Jointure spatiale entre les POINTS des quartiers et les POLYGONES des arrondissements
df_correspondance = gpd.sjoin(quartiers_points, df_arrondissements_geo, how="left", predicate="intersects")


# 4. Nettoyer pour n'avoir que le mapping (VAR5 <-> Code Arrondissement)
# On récupère VAR5 (le code quartier ex: L7501.75229) et le nom de l'arrondissement
mapping = df_correspondance[['VAR5', 'c_ar']]



# 5. Conversion du mapping en Polars
mapping_pl = pl.from_pandas(mapping)

# Chargement du mapping en CSV pour faire correspondre les code de quartiers aux codes de zone pour récupérer les loyers médians
mapping_zone = pl.read_excel("./data/bronze/rent_data/table_zones_2024_L7501_1.xls", has_header=True)

#Jointure entre le mapping spatial et le mapping de correspondance des zones pour récupérer les codes de quartiers associés à chaque zone de calcul
mapping_pl = mapping_pl.join(mapping_zone, left_on="VAR5", right_on="var5", how="inner")

# 6. Charger tes données de loyers (Bronze)
loyers = pl.read_csv("./data/bronze/rent_data/Base_OP_2024_L7501.csv", separator=";", encoding="latin1")


loyers = loyers.filter(
    (pl.col("epoque_construction_local").is_null()) & 
    (pl.col("epoque_construction_homogene").is_null()) )

# on ne garde que les colonnes qui nous intéressent
loyers = loyers.select([
    "Zone_calcul", 
    "loyer_median", 
    "loyer_1_quartile", 
    "loyer_3_quartile"
])


# 7. Jointure finale
# On lie le loyer du quartier à son arrondissement via le mapping spatial
loyers_complets = loyers.join(mapping_pl, left_on="Zone_calcul", right_on="var4")

loyers_complets.write_csv("./data/silver/rent_data_complet.csv", separator=";")










# A mettre dans le gold peut être ? 
# 8. Agrégation par Arrondissement
loyers_complets = loyers_complets.with_columns([
    pl.col("loyer_median").str.replace(",", ".").cast(pl.Float64, strict=False),
    pl.col("loyer_1_quartile").str.replace(",", ".").cast(pl.Float64, strict=False),
    pl.col("loyer_3_quartile").str.replace(",", ".").cast(pl.Float64, strict=False)
])

# Agrégation par code d'arrondissement (c_ar)
loyers_par_arrdt = (
    loyers_complets.group_by("c_ar")
    .agg([
        pl.col("loyer_median").mean().round(2).alias("loyer_median_m2"),
        pl.col("loyer_1_quartile").mean().round(2).alias("loyer_q1_m2"),
        pl.col("loyer_3_quartile").mean().round(2).alias("loyer_q3_m2")
    ])
    .sort("c_ar")
)

# loyers_par_arrdt.write_csv("./data/silver/rent_data_par_arrdt.csv", separator=";")