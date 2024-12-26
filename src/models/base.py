from datetime import datetime, timezone
from enum import EnumType

from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import DateTime, func
import logging


log = logging.getLogger(__name__)


class Base(DeclarativeBase):
    __abstract__ = True

    repr_columns = ["id"]

    def __repr__(self) -> str:
        cols = []
        for col in self.repr_columns:
            if isinstance(getattr(self, col), EnumType):
                cols.append(f"{col}={getattr(self, col).value}")
            else:
                cols.append(f"{col}={getattr(self, col)}")
        return " ".join(cols)


class CUDMixin(Base):
    __abstract__ = True
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=datetime.now(timezone.utc),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        default=datetime.now(timezone.utc),
        onupdate=datetime.now(timezone.utc),
    )
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))


class IdMixin(Base):
    __abstract__ = True
    id: Mapped[int] = mapped_column(primary_key=True)


class IdCUDMixin(CUDMixin, IdMixin):
    __abstract__ = True
