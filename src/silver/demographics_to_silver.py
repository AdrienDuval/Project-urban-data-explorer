"""Compatibility shim — canonical code lives under ``src/indicators/``."""

from src.indicators.demographics.silver import process_demographics_silver  # noqa: F401

__all__ = ['process_demographics_silver']
