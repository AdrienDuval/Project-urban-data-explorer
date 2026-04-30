"""Compatibility shim — canonical code lives under ``src/indicators/``."""

from src.indicators.thermal_comfort.gold import process_thermal_comfort_gold  # noqa: F401

__all__ = ['process_thermal_comfort_gold']
