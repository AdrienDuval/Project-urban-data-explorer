"""Compatibility shim — canonical code lives under ``src/indicators/``."""

from src.indicators.vivabilite_familiale.silver.schools import process_schools  # noqa: F401

__all__ = ['process_schools']
