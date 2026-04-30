"""Compatibility shim — canonical code lives under ``src/indicators/``."""

from src.indicators.foundation.iris import process_iris  # noqa: F401

__all__ = ['process_iris']
