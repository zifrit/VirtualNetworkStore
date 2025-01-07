from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder


def list_user_virtual_networks_inline_buttons_builder(
    user_virtual_network_keys: list[str],
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for virtual_network_key in user_virtual_network_keys:
        builder.row(
            InlineKeyboardButton(
                text=virtual_network_key,
                callback_data=virtual_network_key,
            )
        )
    builder.row(
        InlineKeyboardButton(
            text="🔙 Назад",
            callback_data="back_to_start_menu",
        )
    )
    return builder.as_markup()


def user_virtual_network_inline_buttons_builder(
    user_virtual_network_key: str,
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="Добавить трафик",
            callback_data=f"extend_traffic-{user_virtual_network_key}",
        ),
        InlineKeyboardButton(
            text="Удалить виртуальную сеть",
            callback_data=f"delete_virtual_network-{user_virtual_network_key}",
        ),
        width=2,
    )
    builder.row(
        InlineKeyboardButton(
            text="🔙 Назад",
            callback_data="back_to_list_user_virtual_networks",
        ),
    )
    return builder.as_markup()


def extend_virtual_network_traffic_inline_buttons_builder(
    tariffs: list[dict[str, str]],
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for tariff in tariffs:
        builder.row(
            InlineKeyboardButton(
                text=f"{tariff["traffic_limit"]}гб",
                callback_data=f"add_traffic-{tariff["tariff_key"]}",
            ),
        )
    builder.row(
        InlineKeyboardButton(
            text="🔙 Назад",
            callback_data="back_to_list_user_virtual_networks",
        ),
    )
    return builder.as_markup()


def user_validate_extend_virtual_network_traffic_inline_buttons(
    user_id: int, order_id: int
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅",
            callback_data=f"user_approve_extend_virtual_network_traffic-{user_id}-{order_id}",
        ),
        InlineKeyboardButton(
            text="❌",
            callback_data=f"user_cancel_extend_virtual_network_traffic-{user_id}-{order_id}",
        ),
        width=2,
    )
    return builder.as_markup()


def admin_validate_extend_virtual_network_traffic_inline_buttons(
    user_id: int, order_id: int
) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(
            text="✅Оплатил",
            callback_data=f"admin_approve_extend_virtual_network_traffic-{user_id}-{order_id}",
        ),
        InlineKeyboardButton(
            text="❌Не оплатил",
            callback_data=f"admin_cancel_extend_virtual_network_traffic-{user_id}-{order_id}",
        ),
        width=2,
    )
    return builder.as_markup()
