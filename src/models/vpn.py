import typing
import enum
from datetime import datetime
from src.models.base import IdCUDMixin
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import String, ForeignKey, DateTime, Enum

if typing.TYPE_CHECKING:
    from src.models.user import TgUser
    from src.models.order import Order


class StatusVPN(enum.Enum):
    active = "active"
    inactive = "inactive"


class TypeVPN(enum.Enum):
    vmess = "vmess"
    vless = "vless"
    trojan = "trojan"
    shadowsocks = "shadowsocks"


class UserVPNs(IdCUDMixin):
    __tablename__ = "user_vpn_s"
    vpn_key: Mapped[str] = mapped_column(String(255), unique=True)
    status: Mapped[StatusVPN] = mapped_column(
        Enum(StatusVPN, name="status_user_vpn"),
        comment="Состояние купленного впн",
    )
    type_VPN: Mapped[TypeVPN] = mapped_column(
        Enum(TypeVPN, name="type_user_vpn"),
        comment="Тип впн",
    )
    vpn: Mapped[str] = mapped_column(String(255))
    expire: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    tg_user_id: Mapped[int] = mapped_column(ForeignKey("tg_users.id"))
    tg_user: Mapped["TgUser"] = relationship(back_populates="user_vpn_s")

    repr_columns = ["id", "vpn_key"]


class Country(IdCUDMixin):
    __tablename__ = "countries"
    view_country: Mapped[str] = mapped_column(String(255))
    key_country: Mapped[str] = mapped_column(String(255), unique=True)
    prices: Mapped[list["Price"]] = relationship(
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


class Price(IdCUDMixin):
    __tablename__ = "prices"
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
    price_key: Mapped[str | None] = mapped_column(
        String(255), comment="Ключ для цены", unique=True
    )
    traffic_limit: Mapped[int] = mapped_column(
        comment="Объем разрешённого трафика", default=200, server_default="200"
    )
    country_id: Mapped[int] = mapped_column(ForeignKey("countries.id"))
    is_active: Mapped[bool] = mapped_column(comment="Статус цены")
    country: Mapped["Country"] = relationship(back_populates="prices")
    orders: Mapped[list["Order"]] = relationship(back_populates="price")

    repr_columns = ["id", "view_price"]
