"""
Bronze → Silver: Paris population

Reads the INSEE census file, filters to Paris residential IRIS zones,
and keeps only the columns needed downstream.
"""
import pandas as pd

from src.config import MIN_POPULATION, POPULATION_RAW, POPULATION_SILVER


def process_population() -> pd.DataFrame:
    """
    Extract residential population per IRIS zone for Paris.

    Filters:
    - COM starts with '75'  (Paris only — no DEP column in 2022 CSV)
    - TYP_IRIS == 'H'  (residential zones only, excludes activity/mixed zones)
    - population > MIN_POPULATION  (drops near-empty zones)

    Returns:
        DataFrame with columns: IRIS, LAB_IRIS, population
    """
    df = pd.read_csv(POPULATION_RAW, sep=";", dtype={"IRIS": str, "COM": str, "LAB_IRIS": str})

    paris = df[df["COM"].str.startswith("75")].copy()
    paris = paris[paris["TYP_IRIS"] == "H"]

    paris = paris[["IRIS", "LAB_IRIS", "P22_POP_FR"]]
    paris = paris.rename(columns={"P22_POP_FR": "population"})
    paris = paris[paris["population"] > MIN_POPULATION]

    paris.to_csv(POPULATION_SILVER, index=False)
    print(f"[population] {len(paris)} IRIS zones saved → {POPULATION_SILVER.name}")
    return paris
