"""
Bronze → Silver: IRIS zones

Reads the raw IRIS Excel file and filters it to Paris only (DEP = 75).
"""
import pandas as pd

from src.config import IRIS_RAW, IRIS_SILVER


def process_iris() -> pd.DataFrame:
    """
    Filter IRIS zones to Paris (DEP=75) and save to silver.

    Returns:
        DataFrame of Paris IRIS zones.
    """
    iris = pd.read_excel(IRIS_RAW)
    iris_paris = iris[iris["DEP"] == 75].copy()

<<<<<<< Updated upstream
    iris_paris.to_csv(IRIS_SILVER, index=False)
    print(f"[iris] {len(iris_paris)} IRIS zones saved → {IRIS_SILVER.name}")
=======
    Path(IRIS_SILVER).parent.mkdir(parents=True, exist_ok=True)

    iris_paris.to_csv(IRIS_SILVER, index=False,)
    # print(f"[iris] {len(iris_paris)} IRIS zones saved → {IRIS_SILVER.name}")
>>>>>>> Stashed changes
    return iris_paris
