from src.models.vpn import BillingPeriod, Currency
from src.schemas.base import BaseSchema


class BaseCountriesSchema(BaseSchema):
    view_country: str
    key_country: str


class ShowCountriesSchema(BaseCountriesSchema):
    pass


class BasePricesSchema(BaseSchema):
    view_price: str
    term: int
    billing_period: BillingPeriod
    price: int
    currency: Currency
    traffic_limit: int
    price_key: str
    country_id: int
    is_active: bool


class ShowPricesSchema(BasePricesSchema):
    pass


class ShortShowPriceSchema(BaseSchema):
    view_price: str
    term: int
    traffic_limit: int
    billing_period: BillingPeriod
