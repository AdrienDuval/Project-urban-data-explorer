"""Compatibility shim — canonical code lives under ``src/indicators/``."""

from src.indicators.vivabilite_familiale.gold.school_density import compute_school_density  # noqa: F401

__all__ = ['compute_school_density']
