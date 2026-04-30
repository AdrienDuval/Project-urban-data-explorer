"""Compatibility shim — canonical code lives under ``src/indicators/transport/transport_score.py``."""

from src.indicators.transport.transport_score import compute_transport_score  # noqa: F401
from src.indicators.transport.transport_score import compute_transport_indicator_score  # noqa: F401

__all__ = ["compute_transport_score", "compute_transport_indicator_score"]
