"""Compatibility shim — canonical code lives under ``src/indicators/``."""

from src.indicators.bdcom.silver import process_bdcom  # noqa: F401

__all__ = ['process_bdcom']
