from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload

from src.models.order import Order
from src.crud.base import BaseManager


class OrderManager(BaseManager[Order]):

    async def get_by_id_with_tariff(
        self, session: AsyncSession, id_: int, *args, **kwargs
    ) -> Order:
        result = await session.scalar(
            select(self._model)
            .options(joinedload(Order.tariff))
            .where(
                self._model.id == id_,
                self._model.deleted_at.is_(None),
            )
        )
        return result


order_manager = OrderManager(Order)
