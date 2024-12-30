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


def choice_country_tariff_inline_buttons_builder(
    prices: list[dict],
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for price in prices:
        builder.row(
            InlineKeyboardButton(
                text=price["back_text"],
                callback_data=price["back_callback_data"],
            )
        )
    builder.row(
        InlineKeyboardButton(
            text="🔙 Назад",
            callback_data="back_to_choice_county",
        )
    )
    return builder.as_markup()
