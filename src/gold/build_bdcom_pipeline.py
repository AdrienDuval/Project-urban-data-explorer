"""Compatibility shim — canonical code lives under ``src/indicators/``."""

from src.indicators.bdcom.gold import process_bdcom_gold  # noqa: F401
from src.indicators.bdcom.gold import export_to_gold  # noqa: F401
from src.indicators.bdcom.gold import _assign_code_iris_from_points  # noqa: F401

__all__ = ['process_bdcom_gold', 'export_to_gold', '_assign_code_iris_from_points']
