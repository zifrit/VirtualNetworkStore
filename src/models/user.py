import typing

from src.models.base import IdCUDMixin
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import String, BigInteger, ForeignKey, Boolean

if typing.TYPE_CHECKING:
    from src.models.vpn import UserVirtualNetworks
    from src.models.order import Order


class TgUser(IdCUDMixin):
    __tablename__ = "tg_users"
    username: Mapped[str] = mapped_column(String(255))
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True)
    user_virtual_networks: Mapped[list["UserVirtualNetworks"]] = relationship(
        back_populates="tg_user"
    )
    # # Рефералы, которых пригласил данный пользователь
    referred_users: Mapped[list["Referral"]] = relationship(
        "Referral",
        back_populates="referrer",
        foreign_keys="[Referral.referrer_id]",
    )
    # Пользователь, который пригласил текущего пользователя
    invited_by: Mapped[list["Referral"]] = relationship(
        "Referral",
        back_populates="referred_user",
        foreign_keys="[Referral.referred_user_id]",
    )
    orders: Mapped[list["Order"]] = relationship(back_populates="tg_user")
    is_admin: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        comment="Является ли админом",
    )
    is_admin_panel: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default="false",
        comment="Может ли зайти в админ панель",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default="true",
        comment="Активен ли пользователь",
    )

    repr_columns = ["tg_id", "username"]


class Referral(IdCUDMixin):
    __tablename__ = "referrals"
    # Реферал, который пригласил данный пользователь
    # Тот кого пригласили
    referrer_id: Mapped[int] = mapped_column(ForeignKey("tg_users.id"))
    # Пользователь, который пригласил текущего пользователя
    # Тот кто пригласил
    referred_user_id: Mapped[int] = mapped_column(ForeignKey("tg_users.id"))

    referrer: Mapped["TgUser"] = relationship(
        back_populates="referred_users",
        foreign_keys=[referrer_id],
    )

    referred_user: Mapped["TgUser"] = relationship(
        back_populates="invited_by",
        foreign_keys=[referred_user_id],
    )
