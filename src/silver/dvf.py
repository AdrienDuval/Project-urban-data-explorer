"""Compatibility shim — canonical code lives under ``src/indicators/``."""

from src.indicators.dvf.silver import process_dvf  # noqa: F401

__all__ = ['process_dvf']
