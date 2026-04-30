"""Shared geometry and population layers used across indicators."""

from src.indicators.foundation.iris import process_iris
from src.indicators.foundation.population import process_population
from src.indicators.foundation.reference import load_reference_tables

__all__ = ["process_iris", "process_population", "load_reference_tables"]
