from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Tariff, Country
from src.crud.base import BaseManager


class TariffManager(BaseManager[Tariff]):

    async def get_country_tariff(
        self,
        db_session: AsyncSession,
        country_id: int,
    ) -> list[Tariff]:
        prices = await db_session.scalars(
            select(self._model).where(
                self._model.country_id == country_id,
                self._model.deleted_at.is_(None),
                self._model.is_active.is_(True),
            )
        )
        return list(prices)

    async def get_tariff_by_tariff_key(
        self,
        db_session: AsyncSession,
        tariff_key: str,
    ) -> Tariff:
        prices = await db_session.scalar(
            select(self._model).where(
                self._model.tariff_key == tariff_key,
                self._model.deleted_at.is_(None),
                self._model.is_active.is_(True),
            )
        )
        return prices


tariff_manager = TariffManager(Tariff)


class CountryManager(BaseManager[Country]):
    pass


country_manager = CountryManager(Country)
