"""Compatibility shim — canonical code lives under ``src/indicators/``."""

from src.indicators.foundation.reference import load_reference_tables  # noqa: F401

__all__ = ['load_reference_tables']
