from src.models.marzban import MarzbanService
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.crud.base import BaseManager


class MarzbanServiceManager(BaseManager[MarzbanService]):
    async def get_lower_count_users(self, session: AsyncSession) -> MarzbanService:
        result = await session.scalars(
            select(self._model)
            .where(self._model.is_active == True)
            .order_by(MarzbanService.count_users)
        )
        return result.first()

    async def get_services(self, session: AsyncSession) -> list[str]:
        result = await session.scalars(
            select(self._model.name).where(self._model.is_active == True)
        )
        return list(result)


marzban_service_manager = MarzbanServiceManager(MarzbanService)
