"""Compatibility shim — canonical code lives under ``src/indicators/transport/silver.py``."""

from src.indicators.transport.silver import process_transport  # noqa: F401
from src.indicators.transport.silver import process_transport_arrets  # noqa: F401
from src.indicators.transport.silver import process_velib  # noqa: F401

__all__ = ["process_transport", "process_transport_arrets", "process_velib"]
