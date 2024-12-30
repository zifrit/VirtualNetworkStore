from src.models.order import Order
from src.crud.base import BaseManager


class OrderManager(BaseManager[Order]):
    pass


order_manager = OrderManager(Order)
