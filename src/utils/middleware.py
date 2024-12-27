from typing import Callable, Dict, Any, Awaitable
from aiogram import BaseMiddleware
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.db_connections import db_session


class BaseDatabaseMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[Message | CallbackQuery, Dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: Dict[str, Any],
    ) -> Any:
        async with db_session.session_factory() as session:
            self.set_session(data, session)
            try:
                result = await handler(event, data)
                await self.after_handler(session)
                return result
            except Exception as e:
                await session.rollback()
                raise e
            finally:
                await session.close()

    def set_session(self, data: Dict[str, Any], session: AsyncSession) -> None:
        """Метод для установки сессии в словарь данных."""
        raise NotImplementedError("Этот метод должен быть реализован в подклассах.")

    async def after_handler(self, session: AsyncSession) -> None:
        """Метод для выполнения действий после вызова хендлера (например, коммит)."""
        pass


class DatabaseMiddleware(BaseDatabaseMiddleware):
    def set_session(self, data: Dict[str, Any], session: AsyncSession) -> None:
        data["db_session"] = session

    async def after_handler(self, session) -> None:
        await session.commit()
