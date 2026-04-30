"""Demographics silver tables → gold map scores."""

from src.indicators.demographics.gold import process_demographics_gold
from src.indicators.demographics.silver import process_demographics_silver

__all__ = ["process_demographics_silver", "process_demographics_gold"]
