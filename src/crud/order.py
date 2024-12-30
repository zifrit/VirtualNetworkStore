from src.models.order import Order, OrderReceipt
from src.crud.base import BaseManager


class OrderManager(BaseManager[Order]):
    pass


order_manager = OrderManager(Order)


class OrderReceiptManager(BaseManager[OrderReceipt]):
    pass


order_receipt_manger = OrderReceiptManager(OrderReceipt)
