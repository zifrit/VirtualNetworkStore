import typing
import enum
from datetime import datetime
from src.models.base import IdCUDMixin
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import String, ForeignKey, DateTime, Integer, Text, Boolean
from sqlalchemy.dialects.postgresql import ENUM

if typing.TYPE_CHECKING:
    from src.models.user import TgUser
    from src.models.order import Order
    from src.models.marzban import MarzbanService


class StatusVirtualNetwork(enum.Enum):
    active = "active"
    inactive = "inactive"


class TypeVirtualNetwork(enum.Enum):
    vmess = "vmess"
    vless = "vless"
    trojan = "trojan"
    shadowsocks = "shadowsocks"


class UserVirtualNetworks(IdCUDMixin):
    __tablename__ = "user_virtual_networks"
    virtual_network_key: Mapped[str] = mapped_column(String(255), unique=True)
    status: Mapped[StatusVirtualNetwork] = mapped_column(
        ENUM(StatusVirtualNetwork, name="status_user_virtual_networks"),
        comment="Состояние купленного виртуальной сети",
    )
    type_virtual_networks: Mapped[TypeVirtualNetwork] = mapped_column(
        ENUM(TypeVirtualNetwork, name="type_user_virtual_networks"),
        comment="Тип виртуальной сети",
    )
    virtual_networks: Mapped[str] = mapped_column(Text())
    expire: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    traffic_limit: Mapped[int] = mapped_column(
        comment="Объем разрешённого трафика", default=200, server_default="200"
    )
    tg_used_traffic: Mapped[int] = mapped_column(
        Integer(), comment="Сколько гб пользователь уже израсходовал"
    )
    tg_user_id: Mapped[int] = mapped_column(ForeignKey("tg_users.id"))
    tg_user: Mapped["TgUser"] = relationship(back_populates="user_virtual_networks")

    marzban_service_id: Mapped[int | None] = mapped_column(
        ForeignKey("marzban_services.id")
    )
    marzban_service: Mapped["MarzbanService"] = relationship(
        back_populates="user_virtual_networks"
    )

    notified_low_traffic_data: Mapped[bool] = mapped_column(
        Boolean(), default=False, server_default="false"
    )
    notified_traffic_data_done: Mapped[bool] = mapped_column(
        Boolean(), default=False, server_default="false"
    )
    notified_expired_soon: Mapped[bool] = mapped_column(
        Boolean(), default=False, server_default="false"
    )
    notified_expired_done: Mapped[bool] = mapped_column(
        Boolean(), default=False, server_default="false"
    )

    repr_columns = ["id", "virtual_network_key"]


class BillingPeriod(enum.Enum):
    day = "day"
    month = "month"
    year = "year"


class Currency(enum.Enum):
    dollars = "dollars"
    euro = "euro"
    ruble = "ruble"


class Tariff(IdCUDMixin):
    __tablename__ = "tariffs"
    view_price: Mapped[str] = mapped_column(String(255))
    term: Mapped[int] = mapped_column(
        comment="Количество времени",
        default=1,
    )
    billing_period: Mapped[BillingPeriod] = mapped_column(
        ENUM(BillingPeriod, name="billing_period"),
        comment="Период времени",
        default=BillingPeriod.month,
    )
    price: Mapped[int] = mapped_column(comment="Цена")
    currency: Mapped[Currency] = mapped_column(
        ENUM(Currency, name="price_currency"),
        comment="Валюта",
        default=Currency.ruble,
    )
    traffic_limit: Mapped[int] = mapped_column(
        comment="Объем разрешённого трафика",
        default=200,
    )
    is_active: Mapped[bool] = mapped_column(
        comment="Статус тарифа",
        default=False,
    )
    is_archive: Mapped[bool] = mapped_column(
        comment="в архиве",
        default=False,
    )
    orders: Mapped[list["Order"]] = relationship(back_populates="tariff")

    repr_columns = ["id", "view_price"]
