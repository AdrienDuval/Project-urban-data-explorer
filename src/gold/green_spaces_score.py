"""Compatibility shim — canonical code lives under ``src/indicators/``."""

from src.indicators.vivabilite_familiale.gold.green_spaces_score import compute_green_spaces_score  # noqa: F401

__all__ = ['compute_green_spaces_score']
