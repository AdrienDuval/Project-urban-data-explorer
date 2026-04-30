"""Housing market: median rent and sale price (silver → gold by arrondissement)."""

from src.indicators.housing_market.rent_gold import process_rent_data_to_gold
from src.indicators.housing_market.rent_silver import process_rent_data_to_silver
from src.indicators.housing_market.sale_gold import process_sale_price_median_to_gold
from src.indicators.housing_market.sale_silver import process_sale_price_median_to_silver

__all__ = [
    "process_rent_data_to_silver",
    "process_sale_price_median_to_silver",
    "process_rent_data_to_gold",
    "process_sale_price_median_to_gold",
]
