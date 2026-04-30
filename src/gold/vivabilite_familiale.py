"""Compatibility shim — canonical code lives under ``src/indicators/``."""

from src.indicators.vivabilite_familiale.gold.composite import compute_vivabilite_familiale  # noqa: F401

__all__ = ['compute_vivabilite_familiale']
