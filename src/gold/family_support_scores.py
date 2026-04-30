"""Compatibility shim — canonical code lives under ``src/indicators/``."""

from src.indicators.vivabilite_familiale.gold.family_support_scores import compute_healthcare_score  # noqa: F401
from src.indicators.vivabilite_familiale.gold.family_support_scores import compute_daily_services_score  # noqa: F401
from src.indicators.vivabilite_familiale.gold.family_support_scores import compute_neutral_family_factors  # noqa: F401
from src.indicators.vivabilite_familiale.gold.family_support_scores import compute_family_support_scores  # noqa: F401

__all__ = ['compute_healthcare_score', 'compute_daily_services_score', 'compute_neutral_family_factors', 'compute_family_support_scores']
