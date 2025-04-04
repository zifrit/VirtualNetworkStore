import typing
import enum
from src.models.base import IdCUDMixin
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import ForeignKey, String
from sqlalchemy.dialects.postgresql import ENUM
from src.models.vpn import Currency

if typing.TYPE_CHECKING:
    from src.models.user import TgUser
    from src.models.vpn import Tariff


class OrderStatus(enum.Enum):
    completed = "completed"
    failed = "failed"
    in_progress = "in_progress"
    start = "start"


class OrderType(enum.Enum):
    buy = "buy"  # покупка
    refill_traffic = "refill_traffic"  # пополнение трафика
    refill_expire = "refill_expire"  # пополнение срока жизни


class Order(IdCUDMixin):
    __tablename__ = "orders"
    virtual_network_key: Mapped[str | None] = mapped_column(String(255))
    tariff_id: Mapped[int] = mapped_column(ForeignKey("tariffs.id"))
    tariff: Mapped["Tariff"] = relationship(back_populates="orders")
    amount: Mapped[int] = mapped_column(comment="Сумма")
    tg_user_id: Mapped[int] = mapped_column(ForeignKey("tg_users.id"))
    tg_user: Mapped["TgUser"] = relationship(back_populates="orders")
    currency: Mapped[Currency] = mapped_column(
        ENUM(Currency, name="currency"),
        comment="Валюта",
    )
    status: Mapped[OrderStatus] = mapped_column(
        ENUM(OrderStatus, name="order_status"),
        comment="Статус заказа",
    )
    type: Mapped[OrderType] = mapped_column(
        ENUM(OrderType, name="order_type"),
        comment="Тип заказа",
    )
    repr_columns = ["id", "status", "type"]
