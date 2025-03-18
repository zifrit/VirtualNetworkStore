import asyncio
import logging.config
from aiogram import types

from src.core.db_connections import db_session
from src.crud.user import user_manager
from src.core.settings import bot, dp
from src.core.logger import LOGGING
from src.utils.middleware import DatabaseMiddleware
from src.handlers import (
    start,
    account,
    buy_virtual_network,
    user_virtual_network,
    help,
)
from src.tasks.schedule import scheduler

loger = logging.getLogger(__name__)

commands = [
    types.BotCommand(command="start", description="запуск бота"),
    types.BotCommand(command="menu", description="Меню"),
]


# Функция, которая выполнится когда бот запустится
async def start_bot():
    async with db_session.session_factory() as session:
        for admin_id in await user_manager.get_admins(session=session):
            try:
                scheduler.start()
                await bot.send_message(admin_id, f"Бот запущен")
            except:
                scheduler.shutdown()
                pass
        loger.info("Бот успешно запущен.")


# Функция, которая выполнится когда бот завершит свою работу
async def stop_bot():
    try:
        async with db_session.session_factory() as session:
            for admin_id in await user_manager.get_admins(session=session):
                await bot.send_message(admin_id, "Бот остановлен")
            scheduler.shutdown()
    except:
        pass
    loger.error("Бот остановлен!")


async def main():
    # регистрация роутов
    dp.include_router(start.router)
    dp.include_router(account.router)
    dp.include_router(help.router)
    dp.include_router(user_virtual_network.router)
    dp.include_router(buy_virtual_network.router)

    # регистрация мидлварей
    dp.update.middleware.register(DatabaseMiddleware())

    # регистрация функций
    dp.startup.register(start_bot)
    dp.shutdown.register(stop_bot)

    try:
        await bot.set_my_commands(commands=commands)
        await bot.delete_webhook(drop_pending_updates=True)
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()


if __name__ == "__main__":
    logging.config.dictConfig(LOGGING)
    asyncio.run(main())
