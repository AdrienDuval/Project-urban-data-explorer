"""BDCom commercial premises (silver → gold with IRIS assignment)."""

from src.indicators.bdcom.gold import process_bdcom_gold
from src.indicators.bdcom.silver import process_bdcom

__all__ = ["process_bdcom", "process_bdcom_gold"]
