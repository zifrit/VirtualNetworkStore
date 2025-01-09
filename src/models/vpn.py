import typing
import enum
from datetime import datetime
from src.models.base import IdCUDMixin
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import String, ForeignKey, DateTime, Enum, Integer, Text, Boolean

if typing.TYPE_CHECKING:
    from src.models.user import TgUser
    from src.models.order import Order


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
        Enum(StatusVirtualNetwork, name="status_user_virtual_networks"),
        comment="Состояние купленного виртуальной сети",
    )
    type_virtual_networks: Mapped[TypeVirtualNetwork] = mapped_column(
        Enum(TypeVirtualNetwork, name="type_user_virtual_networks"),
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


class Country(IdCUDMixin):
    __tablename__ = "countries"
    view_country: Mapped[str] = mapped_column(String(255))
    key_country: Mapped[str] = mapped_column(String(255), unique=True)
    tariffs: Mapped[list["Tariff"]] = relationship(
        back_populates="country",
    )

    repr_columns = ["id", "view_country"]


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
    term: Mapped[int] = mapped_column(comment="Количество времени")
    billing_period: Mapped[BillingPeriod] = mapped_column(
        Enum(BillingPeriod, name="billing_period"),
        comment="Период времени",
    )
    price: Mapped[int] = mapped_column(comment="Цена")
    currency: Mapped[Currency] = mapped_column(
        Enum(Currency, name="price_currency"),
        comment="Валюта",
    )
    tariff_key: Mapped[str | None] = mapped_column(
        String(255), comment="Ключ для тарифа", unique=True
    )
    traffic_limit: Mapped[int] = mapped_column(
        comment="Объем разрешённого трафика", default=200, server_default="200"
    )
    country_id: Mapped[int] = mapped_column(ForeignKey("countries.id"))
    is_active: Mapped[bool] = mapped_column(comment="Статус тарифа")
    country: Mapped["Country"] = relationship(back_populates="tariffs")
    orders: Mapped[list["Order"]] = relationship(back_populates="tariff")

    repr_columns = ["id", "view_price"]
