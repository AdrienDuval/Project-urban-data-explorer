"""
Vivabilité familiale: multi-pillar composite.

**Transport** is its own indicator (:mod:`src.indicators.transport`); this package
only **consumes** ``TRANSPORT_SCORE_GOLD`` when building the composite.
"""

from src.indicators.vivabilite_familiale.gold import (
    compute_family_support_scores,
    compute_green_spaces_score,
    compute_school_density,
    compute_services_score,
    compute_vivabilite_familiale,
)

__all__ = [
    "compute_school_density",
    "compute_services_score",
    "compute_green_spaces_score",
    "compute_family_support_scores",
    "compute_vivabilite_familiale",
]
