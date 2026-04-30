"""Compatibility shim — canonical code lives under ``src/indicators/``."""

from src.indicators.housing_market.rent_silver import process_rent_data_to_silver  # noqa: F401

__all__ = ['process_rent_data_to_silver']
