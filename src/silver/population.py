"""
Bronze → Silver: Paris population

Reads the INSEE census file, filters to Paris residential IRIS zones,
and keeps only the columns needed downstream.
"""
import pandas as pd

from src.config import POPULATION_RAW, POPULATION_SILVER, MIN_POPULATION


def process_population() -> pd.DataFrame:
    """
    Extract residential population per IRIS zone for Paris.

    Filters:
    - DEP == '75'  (Paris only)
    - TYP_IRIS == 'H'  (residential zones only, excludes activity/mixed zones)
    - population > MIN_POPULATION  (drops near-empty zones)

    Returns:
        DataFrame with columns: IRIS, LIBCOM, LIBIRIS, GRD_QUART, population
    """
    # The census file has 5 metadata rows before the actual header
    df = pd.read_excel(POPULATION_RAW, header=5, sheet_name="IRIS")

    paris = df[df["DEP"] == "75"].copy()
    paris = paris[paris["TYP_IRIS"] == "H"]

    paris = paris[["IRIS", "LIBCOM", "LIBIRIS", "GRD_QUART", "P19_POP_FR"]]
    paris = paris.rename(columns={"P19_POP_FR": "population"})
    paris = paris[paris["population"] > MIN_POPULATION]

    paris.to_csv(POPULATION_SILVER, index=False)
    print(f"[population] {len(paris)} IRIS zones saved → {POPULATION_SILVER.name}")
    return paris
