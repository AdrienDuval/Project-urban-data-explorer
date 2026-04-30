"""Compatibility shim — canonical code lives under ``src/indicators/``."""

from src.indicators.vivabilite_familiale.silver.green_spaces import process_green_spaces  # noqa: F401

__all__ = ['process_green_spaces']
