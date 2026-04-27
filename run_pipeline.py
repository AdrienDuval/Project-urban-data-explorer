"""
Entry point for the indice_familiale pipeline.

Usage
-----
Run the full pipeline (bronze → silver → gold):
    python run_pipeline.py

Run only the bronze → silver step:
    python run_pipeline.py --silver

Run only the silver → gold step (requires silver to exist):
    python run_pipeline.py --gold
"""
import argparse

from src.data_loader import load_data
from src.gold.reference import load_reference_tables
from src.gold.school_density import compute_school_density
from src.silver.bdcom import process_bdcom
from src.silver.dvf import process_dvf
from src.silver.hospitals import process_hospitals
from src.silver.iris import process_iris
from src.silver.population import process_population
from src.silver.rent_data_to_silver import process_rent_data_to_silver
from src.silver.schools import process_schools
from src.silver.thermal_comfort_to_silver import process_thermal_comfort_silver
from src.gold.thermal_comfort_to_gold import process_thermal_comfort_gold
from src.gold.sale_price_median_to_gold import process_sale_price_median_to_gold
from src.silver.sale_price_median_to_silver import process_sale_price_median_to_silver
from src.gold.rent_data_to_gold import process_rent_data_to_gold


def run_bronze() -> None:
    print("─" * 40)
    print("Download → Bronze")
    print("─" * 40)
    load_data()


def run_silver() -> None:
    print("─" * 40)
    print("Bronze → Silver")
    print("─" * 40)
    process_iris()
    process_population()
    process_schools()
    process_dvf()
    process_bdcom()
    process_hospitals()
    process_thermal_comfort_silver()
    process_sale_price_median_to_silver()
    process_rent_data_to_silver()


def run_gold() -> None:
    print("─" * 40)
    print("Silver → Gold")
    print("─" * 40)
    load_reference_tables()
    compute_school_density()
    process_thermal_comfort_gold()
    process_sale_price_median_to_gold()
    process_rent_data_to_gold()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the indice familiale pipeline.")
    parser.add_argument("--silver", action="store_true", help="Run bronze→silver only")
    parser.add_argument("--gold",   action="store_true", help="Run silver→gold only")
    args = parser.parse_args()

    if args.silver:
        run_silver()
    elif args.gold:
        run_gold()
    else:
        run_bronze()
        run_silver()
        run_gold()
