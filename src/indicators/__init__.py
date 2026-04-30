"""Indicator-scoped pipeline code (Bronze→Silver→Gold) grouped for demos and docs.

Each subpackage under :mod:`src.indicators` is one *presentable* slice of the
pipeline. Import from here in application code, or follow the README to walk
stages top-to-bottom for a single indicator.

``LEGACY_SHIMS`` lists old import paths (``src.silver.*`` / ``src.gold.*``) that
still work via thin re-export modules.
"""

from __future__ import annotations

# Presentation order: shared base first, then standalone indicators, composite last.
INDICATOR_PACKAGE_ORDER: tuple[str, ...] = (
    "src.indicators.foundation",
    "src.indicators.transport",
    "src.indicators.thermal_comfort",
    "src.indicators.housing_market",
    "src.indicators.demographics",
    "src.indicators.dvf",
    "src.indicators.bdcom",
    "src.indicators.vivabilite_familiale",
)

LEGACY_SHIM_PREFIXES: tuple[str, ...] = ("src.silver.", "src.gold.")

__all__ = [
    "INDICATOR_PACKAGE_ORDER",
    "LEGACY_SHIM_PREFIXES",
]
