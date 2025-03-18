import logging
from aiogram import Router, F
from aiogram.enums import ParseMode
from aiogram.types import CallbackQuery

from src.kbs.other import move_to


loger = logging.getLogger("admin_log")


router = Router()


@router.callback_query(F.data == "android_help")
@router.callback_query(F.data == "apple_help")
async def start_handler(call: CallbackQuery):
    await call.message.edit_text(
        parse_mode=ParseMode.MARKDOWN,
        text="""
🔒 КАК НАСТРОИТЬ СЕТЬ НА ANDROID | [V2ray](https://play.google.com/store/apps/details?id=com.v2ray.ang)

Привет! Сегодня расскажем, как легко настроить VPN на твоём Android-смартфоне.

🎯 ШАГ 1: СКАЧИВАЕМ
• Открой Google Play
• Найди [V2ray](https://play.google.com/store/apps/details?id=com.v2ray.ang)
• Нажми “Установить”

🎯 ШАГ 2: ПОЛУЧАЕМ КЛЮЧ
• Открой нашего бота
• Нажми “Приобрести ключ”
• Скопируй ключ

🎯 ШАГ 3: НАСТРАИВАЕМ
• Открой [V2ray](https://play.google.com/store/apps/details?id=com.v2ray.ang)
• Нажми “Добавить”
• Выбери “Импортировать из буфера”
• Нажми “ОК”

🎯 ШАГ 4: ПОДКЛЮЧАЕМСЯ
• Нажми кнопку “Подключить”
• Дождись надписи “Подключено”

💡 ЕСЛИ ЧТО-ТО НЕ ТАК:
• Перезапусти приложение
• Переустанови ключ
• Перезапусти телефон

🔐 ВАЖНО:
• Храни ключ в безопасности
• Не показывай его другим
• При проблемах пиши в поддержку :@Mishka0777
    """,
        reply_markup=move_to(text="Назад 🔙", callback_data="back_to_start_menu"),
    )
