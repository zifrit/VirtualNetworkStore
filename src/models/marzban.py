import typing

from src.models.base import IdCUDMixin
from sqlalchemy.orm import mapped_column, Mapped, relationship
from sqlalchemy import String, ForeignKey, DateTime, Integer, Text, Boolean

if typing.TYPE_CHECKING:
    from models import UserVirtualNetworks


class MarzbanService(IdCUDMixin):
    __tablename__ = "marzban_services"

    name: Mapped[str] = mapped_column(String(255))
    count_users: Mapped[int] = mapped_column(Integer)
    user_virtual_networks: Mapped[list["UserVirtualNetworks"]] = relationship(
        back_populates="marzban_service"
    )

    repr_columns = ["id", "name"]
