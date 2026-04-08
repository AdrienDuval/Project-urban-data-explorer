import polars as pl

df_sample  = pl.read_csv("Donnees-detaillees-au-logement-du-repertoire-des-logements-locatifs-des-bailleurs-sociau.2025-01.csv", separator=";")


df_paris = df_sample.filter(pl.col("Département - Code de la zone") == "75")

df_paris.write_csv("paris.csv", separator=";")


