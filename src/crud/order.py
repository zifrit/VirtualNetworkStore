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

    async def get_first_order_by_virtual_network_key_with_tariff(
        self, session: AsyncSession, virtual_network_key: int, *args, **kwargs
    ) -> Order:
        result = await session.scalar(
            select(self._model)
            .options(joinedload(Order.tariff))
            .where(
                self._model.virtual_network_key == virtual_network_key,
                self._model.deleted_at.is_(None),
            )
            .order_by(self._model.created_at)
            .limit(1)
        )
        return result


order_manager = OrderManager(Order)
