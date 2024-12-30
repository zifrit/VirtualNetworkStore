from src.models import Price, Country
from src.crud.base import BaseManager


class PriceManager(BaseManager[Price]):
    pass


price_manager = PriceManager(Price)


class CountryManager(BaseManager[Country]):
    pass


country_manager = CountryManager(Country)
