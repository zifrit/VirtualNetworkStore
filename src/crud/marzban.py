from src.models.marzban import MarzbanService
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.crud.base import BaseManager


class MarzbanServiceManager(BaseManager[MarzbanService]):
    async def get_lower_count_users(self, session: AsyncSession) -> MarzbanService:
        result = await session.scalars(
            select(self._model).order_by(MarzbanService.count_users)
        )
        return result.first()

    async def get_services(self, session: AsyncSession) -> list[str]:
        result = await session.scalars(select(self._model.name))
        return list(result)


marzban_service_manager = MarzbanServiceManager(MarzbanService)
