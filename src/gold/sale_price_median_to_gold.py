import geopandas as gpd
import pandas as pd
from src.config import SALE_PRICE_SILVER, SALE_PRICE_GOLD, ARRONDISSEMENTS
from src.db import engine
import os



def process_sale_price_median_to_gold():

    df_price = pd.read_csv(SALE_PRICE_SILVER, sep=";")
    df_arrdt = gpd.read_file(ARRONDISSEMENTS)

    gdf_merged = df_arrdt.merge(df_price, left_on="c_ar", right_on="arrondissement")

    gdf_merged.to_parquet(SALE_PRICE_GOLD, engine="pyarrow")


    SALE_PRICE_GOLD.to_sql("vivabilite_familiale", engine, if_exists="replace", index=False)

    return SALE_PRICE_GOLD



if __name__ == "__main__":
    process_sale_price_median_to_gold()