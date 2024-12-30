from src.models.order import OrderReceiptStatus
from src.models.vpn import Currency
from src.schemas.base import BaseSchema
from src.schemas.user import ShowTgUserSchema
from src.schemas.price import ShortShowPriceSchema


class BaseOrderSchema(BaseSchema):
    price_id: int
    tg_user_id: int
    status: bool


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


class OrderReceiptSchema(BaseSchema):
    currency: Currency
    status: OrderReceiptStatus
    amount: int
    order_id: int


class CreateOrderReceiptSchema(OrderReceiptSchema):
    pass
