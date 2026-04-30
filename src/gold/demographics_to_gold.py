"""Compatibility shim — canonical code lives under ``src/indicators/``."""

from src.indicators.demographics.gold import process_demographics_gold  # noqa: F401

__all__ = ['process_demographics_gold']
