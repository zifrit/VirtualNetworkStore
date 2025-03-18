from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


help_inline = InlineKeyboardMarkup(
    inline_keyboard=[
        [
            InlineKeyboardButton(
                text="📱android",
                callback_data="android_help",
            )
        ],
        [
            InlineKeyboardButton(
                text="📱apple",
                callback_data="apple_help",
            ),
        ],
        [
            InlineKeyboardButton(
                text="Назад 🔙",
                callback_data="back_to_start_menu",
            ),
        ],
    ],
    resize_keyboard=True,
    one_time_keyboard=True,
)
