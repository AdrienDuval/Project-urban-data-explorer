"""Compatibility shim — canonical code lives under ``src/indicators/``."""

from src.indicators.foundation.population import process_population  # noqa: F401

__all__ = ['process_population']
