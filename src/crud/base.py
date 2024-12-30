from datetime import datetime, timezone
from typing import Type
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.base import Base
from src.schemas.base import BaseSchema


class BaseManager[Model: Base]:
    def __init__(self, model: Type[Model]):
        self._model = model

    async def get_by_id(
        self, session: AsyncSession, id_: int, *args, **kwargs
    ) -> Model:
        result = await session.scalar(
            select(self._model).where(
                self._model.id == id_,
                self._model.deleted_at.is_(None),
            )
        )
        return result

    async def create(
        self, session: AsyncSession, obj_schema: BaseSchema, *args, **kwargs
    ) -> Model:
        item = self._model(**obj_schema.model_dump())
        session.add(item)
        await session.commit()
        await session.refresh(item)
        return item

    async def delete(self, session: AsyncSession, id_: int, *args, **kwargs):
        item = await self.get_by_id(session, id_=id_)
        item.deleted_at = datetime.now(timezone.utc)
        await session.commit()
