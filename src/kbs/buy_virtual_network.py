from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def choice_tariffs_inline_buttons_builder(
    tariffs: list[dict],
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for tariff in tariffs:
        builder.row(
            InlineKeyboardButton(
                text=tariff["back_text"],
                callback_data=tariff["back_callback_data"],
            )
        )
    builder.row(
        InlineKeyboardButton(
            text="🔙 Назад",
            callback_data="back_to_start_menu",
        )
    )
    return builder.as_markup()


def admin_validate_buy_virtual_network_inline_buttons(
    user_id: int, order_id: int
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅Оплатил",
            callback_data=f"admin_approve_buy_virtual_network-{user_id}-{order_id}",
        ),
        InlineKeyboardButton(
            text="❌Не оплатил",
            callback_data=f"admin_cancel_buy_virtual_network-{user_id}-{order_id}",
        ),
        width=2,
    )
    return builder.as_markup()


def user_validate_buy_virtual_network_inline_buttons(
    user_id: int, order_id: int
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅",
            callback_data=f"user_approve_buy_virtual_network-{user_id}-{order_id}",
        ),
        InlineKeyboardButton(
            text="❌",
            callback_data=f"user_cancel_buy_virtual_network-{user_id}-{order_id}",
        ),
        width=2,
    )
    return builder.as_markup()
