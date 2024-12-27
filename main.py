import asyncio
import logging.config
from aiogram import types

from src.core.settings import bot, dp, bot_settings
from src.core.logger import LOGGING
from src.utils.middleware import DatabaseMiddleware

loger = logging.getLogger(__name__)

commands = [
    types.BotCommand(command="start", description="запуск бота"),
]


# Функция, которая выполнится когда бот запустится
async def start_bot():
    for admin_id in bot_settings.ADMINS:
        try:
            await bot.send_message(admin_id, f"Бот запущен")
        except:
            pass
    loger.info("Бот успешно запущен.")


# Функция, которая выполнится когда бот завершит свою работу
async def stop_bot():
    try:
        for admin_id in bot_settings.ADMINS:
            await bot.send_message(admin_id, "Бот остановлен")
    except:
        pass
    loger.error("Бот остановлен!")


async def main():

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
