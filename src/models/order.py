import typing
import enum
from src.models.base import IdCUDMixin
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import ForeignKey, Enum
from src.models.vpn import Currency

if typing.TYPE_CHECKING:
    from src.models.user import TgUser
    from src.models.vpn import Price


class Order(IdCUDMixin):
    __tablename__ = "orders"

    price_id: Mapped[int] = mapped_column(ForeignKey("prices.id"))
    price: Mapped["Price"] = relationship(back_populates="orders")
    tg_user_id: Mapped[int] = mapped_column(ForeignKey("tg_users.id"))
    tg_user: Mapped["TgUser"] = relationship(back_populates="orders")
    status: Mapped[bool] = mapped_column(comment="Статус заказа")
    order_receipts: Mapped[list["OrderReceipt"]] = relationship(back_populates="order")

    repr_columns = ["id", "status"]


class OrderReceiptStatus(enum.Enum):
    completed = "completed"
    failed = "failed"
    in_progress = "in_progress"


class OrderReceipt(IdCUDMixin):
    __tablename__ = "order_receipts"

    currency: Mapped[Currency] = mapped_column(
        Enum(Currency, name="currency"),
        comment="Валюта",
    )
    status: Mapped[OrderReceiptStatus] = mapped_column(
        Enum(OrderReceiptStatus, name="order_receipt_status"),
        comment="Статус платежа",
    )
    amount: Mapped[int] = mapped_column(comment="Сумма")
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"))
    order: Mapped["Order"] = relationship(back_populates="order_receipts")
