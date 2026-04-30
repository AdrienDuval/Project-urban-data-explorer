"""Compatibility shim — canonical code lives under ``src/indicators/``."""

from src.indicators.housing_market.sale_silver import process_sale_price_median_to_silver  # noqa: F401

__all__ = ['process_sale_price_median_to_silver']
