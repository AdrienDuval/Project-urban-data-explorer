"""Compatibility shim — canonical code lives under ``src/indicators/transport/transport_points.py``."""

from src.indicators.transport.transport_points import compute_transport_points  # noqa: F401

__all__ = ["compute_transport_points"]
