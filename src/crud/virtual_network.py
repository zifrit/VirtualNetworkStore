from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Tariff, Country, UserVirtualNetworks
from src.crud.base import BaseManager


class TariffManager(BaseManager[Tariff]):

    async def get_country_tariff(
        self,
        session: AsyncSession,
        country_id: int,
    ) -> list[Tariff]:
        prices = await session.scalars(
            select(self._model).where(
                self._model.country_id == country_id,
                self._model.deleted_at.is_(None),
                self._model.is_active.is_(True),
            )
        )
        return list(prices)

    async def get_tariff_by_tariff_key(
        self,
        session: AsyncSession,
        tariff_key: str,
    ) -> Tariff:
        prices = await session.scalar(
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


class UserVirtualNetworksManager(BaseManager[UserVirtualNetworks]):

    async def get_user_virtual_network_by_virtual_network_key(
        self, session: AsyncSession, virtual_network_key: str
    ) -> UserVirtualNetworks:
        user_virtual_networks = await session.scalar(
            select(self._model).where(
                self._model.virtual_network_key == virtual_network_key,
                self._model.deleted_at.is_(None),
            )
        )
        return user_virtual_networks


user_virtual_networks_manager = UserVirtualNetworksManager(UserVirtualNetworks)
