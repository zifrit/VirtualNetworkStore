from src.models.order import OrderStatus, OrderType
from src.models.vpn import Currency
from src.schemas.base import BaseSchema
from src.schemas.user import ShowTgUserSchema
from src.schemas.price import ShortShowPriceSchema


class BaseOrderSchema(BaseSchema):
    tariff_id: int
    tg_user_id: int
    currency: Currency
    status: OrderStatus
    type: OrderType
    amount: int


class CreateOrderSchema(BaseOrderSchema):
    pass


class ShowOrderSchema(BaseOrderSchema):
    id: int


class ShowOrderWithTgUserSchema(ShowOrderSchema):
    tg_user: ShowTgUserSchema


class ShowOrderWithPriceSchema(ShowOrderSchema):
    price: ShortShowPriceSchema


class ShowOrderWithTgUserAndPriceSchema(ShowOrderSchema):
    tg_user: ShowTgUserSchema
    price: ShortShowPriceSchema
