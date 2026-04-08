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

from src.gold.school_density import compute_school_density
from src.silver.iris import process_iris
from src.silver.population import process_population
from src.silver.schools import process_schools


def run_silver() -> None:
    print("─" * 40)
    print("Bronze → Silver")
    print("─" * 40)
    process_iris()
    process_population()
    process_schools()


def run_gold() -> None:
    print("─" * 40)
    print("Silver → Gold")
    print("─" * 40)
    compute_school_density()


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
        run_silver()
        run_gold()
