from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload
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

    async def get_active_tariff_by_id(
        self,
        session: AsyncSession,
        tariff_id: int,
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

    async def get_user_virtual_network_by_virtual_network_key_with_marzban(
        self, session: AsyncSession, virtual_network_key: str
    ) -> UserVirtualNetworks:
        user_virtual_networks = await session.scalar(
            select(self._model)
            .options(joinedload(UserVirtualNetworks.marzban_service))
            .where(
                self._model.virtual_network_key == virtual_network_key,
                self._model.deleted_at.is_(None),
            )
        )
        return user_virtual_networks

    async def get_user_virtual_network_by_marzban(
        self, session: AsyncSession, marz_virtual_network_keys: list[str]
    ) -> list[UserVirtualNetworks]:
        user_virtual_networks = await session.scalars(
            select(self._model).where(
                self._model.virtual_network_key.in_(marz_virtual_network_keys),
                self._model.deleted_at.is_(None),
            )
        )
        return list(user_virtual_networks)


user_virtual_networks_manager = UserVirtualNetworksManager(UserVirtualNetworks)
