"""Compatibility shim — canonical code lives under ``src/indicators/``."""

from src.indicators.dvf.gold import process_dvf_gold  # noqa: F401
from src.indicators.dvf.gold import export_to_gold  # noqa: F401

__all__ = ['process_dvf_gold', 'export_to_gold']
