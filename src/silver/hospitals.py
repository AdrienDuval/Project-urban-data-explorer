"""Compatibility shim — canonical code lives under ``src/indicators/``."""

from src.indicators.vivabilite_familiale.silver.hospitals import process_hospitals  # noqa: F401

__all__ = ['process_hospitals']
