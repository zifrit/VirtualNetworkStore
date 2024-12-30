from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Price, Country
from src.crud.base import BaseManager


class PriceManager(BaseManager[Price]):

    async def get_country_price(
        self,
        db_session: AsyncSession,
        country_id: int,
    ) -> list[Price]:
        prices = await db_session.scalars(
            select(self._model).where(
                self._model.country_id == country_id,
                self._model.deleted_at.is_(None),
                self._model.is_active.is_(True),
            )
        )
        return list(prices)

    async def get_price_by_price_key(
        self,
        db_session: AsyncSession,
        price_key: str,
    ) -> Price:
        prices = await db_session.scalar(
            select(self._model).where(
                self._model.price_key == price_key,
                self._model.deleted_at.is_(None),
                self._model.is_active.is_(True),
            )
        )
        return prices


price_manager = PriceManager(Price)


class CountryManager(BaseManager[Country]):
    pass


country_manager = CountryManager(Country)
