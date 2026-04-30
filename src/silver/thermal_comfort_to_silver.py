"""Compatibility shim — canonical code lives under ``src/indicators/``."""

from src.indicators.thermal_comfort.silver import process_thermal_comfort_silver  # noqa: F401

__all__ = ['process_thermal_comfort_silver']
