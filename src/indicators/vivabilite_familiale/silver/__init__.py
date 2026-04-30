"""Silver layers that feed the vivabilité familiale pillar scores (not Transport — see ``src.indicators.transport``)."""

from src.indicators.vivabilite_familiale.silver.green_spaces import process_green_spaces
from src.indicators.vivabilite_familiale.silver.hospitals import process_hospitals
from src.indicators.vivabilite_familiale.silver.schools import process_schools

__all__ = [
    "process_schools",
    "process_hospitals",
    "process_green_spaces",
]
