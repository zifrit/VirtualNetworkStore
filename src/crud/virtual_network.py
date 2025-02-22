from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models import Tariff, UserVirtualNetworks
from src.crud.base import BaseManager


class TariffManager(BaseManager[Tariff]):

    async def get_tariffs(
        self,
        session: AsyncSession,
    ) -> list[Tariff]:
        tariff = await session.scalars(
            select(self._model).where(
                self._model.deleted_at.is_(None),
                self._model.is_active.is_(True),
                self._model.is_archive.is_(False),
            )
        )
        return list(tariff)

    async def get_tariff_by_id(
        self,
        session: AsyncSession,
        tariff_id: str,
    ) -> Tariff:
        tariff = await session.scalar(
            select(self._model).where(
                self._model.id == tariff_id,
                self._model.deleted_at.is_(None),
                self._model.is_active.is_(True),
                self._model.is_archive.is_(False),
            )
        )
        return tariff


tariff_manager = TariffManager(Tariff)


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
