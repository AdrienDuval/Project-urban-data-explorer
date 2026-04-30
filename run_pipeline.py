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
from src.indicators.bdcom import process_bdcom, process_bdcom_gold
from src.indicators.demographics import process_demographics_gold, process_demographics_silver
from src.indicators.dvf import process_dvf, process_dvf_gold
from src.indicators.foundation import (
    load_reference_tables,
    process_iris,
    process_population,
)
from src.indicators.housing_market import (
    process_rent_data_to_gold,
    process_rent_data_to_silver,
    process_sale_price_median_to_gold,
    process_sale_price_median_to_silver,
)
from src.indicators.thermal_comfort import (
    process_thermal_comfort_gold,
    process_thermal_comfort_silver,
)
from src.indicators.transport import (
    compute_transport_indicator_score,
    compute_transport_points,
    compute_transport_score,
    process_transport,
)
from src.indicators.vivabilite_familiale import (
    compute_family_support_scores,
    compute_green_spaces_score,
    compute_school_density,
    compute_services_score,
    compute_vivabilite_familiale,
)
from src.indicators.vivabilite_familiale.silver import (
    process_green_spaces,
    process_hospitals,
    process_schools,
)


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

    process_green_spaces()
    process_transport()
    process_demographics_silver()


def run_gold() -> None:
    print("─" * 40)
    print("Silver → Gold")
    print("─" * 40)
    load_reference_tables()
    compute_school_density()
    process_thermal_comfort_gold()
    process_sale_price_median_to_gold()
    process_rent_data_to_gold()

    compute_transport_score()
    compute_transport_indicator_score()
    compute_transport_points()
    compute_services_score()
    compute_green_spaces_score()
    compute_family_support_scores()
    compute_vivabilite_familiale()
    process_bdcom_gold()
    process_dvf_gold()
    process_demographics_gold()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the indice familiale pipeline.")
    parser.add_argument("--silver", action="store_true", help="Run bronze→silver only")
    parser.add_argument("--gold", action="store_true", help="Run silver→gold only")
    args = parser.parse_args()

    if args.silver:
        run_silver()
    elif args.gold:
        run_gold()
    else:
        run_bronze()
        run_silver()
        run_gold()
