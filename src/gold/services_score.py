"""Compatibility shim — canonical code lives under ``src/indicators/``."""

from src.indicators.vivabilite_familiale.gold.services_score import compute_services_score  # noqa: F401

__all__ = ['compute_services_score']
