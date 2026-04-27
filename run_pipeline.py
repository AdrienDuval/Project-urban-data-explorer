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
from src.gold.green_spaces_score import compute_green_spaces_score
from src.gold.reference import load_reference_tables
from src.gold.school_density import compute_school_density
from src.gold.services_score import compute_services_score
from src.gold.transport_score import (
    compute_transport_indicator_score,
    compute_transport_score,
)
from src.gold.transport_points import compute_transport_points
from src.gold.vivabilite_familiale import compute_vivabilite_familiale
from src.silver.bdcom import process_bdcom
from src.silver.dvf import process_dvf
from src.silver.green_spaces import process_green_spaces
from src.silver.hospitals import process_hospitals
from src.silver.iris import process_iris
from src.silver.population import process_population
from src.silver.schools import process_schools

from src.silver.transport import process_transport

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
    process_green_spaces()
    process_transport()

def run_gold() -> None:
    print("─" * 40)
    print("Silver → Gold")
    print("─" * 40)
    load_reference_tables()
    compute_school_density()
    compute_transport_score()
    compute_transport_indicator_score()
    compute_transport_points()
    compute_services_score()
    compute_green_spaces_score()
    compute_vivabilite_familiale()

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
