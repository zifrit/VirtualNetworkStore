from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def choice_county_inline_buttons_builder(countries: list[dict]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for county in countries:
        builder.row(
            InlineKeyboardButton(
                text=county["text"],
                callback_data=county["callback_data"],
            )
        )
    builder.row(
        InlineKeyboardButton(
            text="🔙 Назад",
            callback_data="back_to_start_menu",
        )
    )
    return builder.as_markup()
