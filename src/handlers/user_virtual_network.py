import logging
from datetime import datetime, timezone, timedelta
from aiogram import Router, F
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.vpn import EnumStatusVirtualNetwork
from src.core.settings import bot_settings
from src.crud.order import order_manager
from src.crud.virtual_network import user_virtual_networks_manager, tariff_manager
from src.kbs.other import move_to
from src.marzban.client import marzban_manager
from src.kbs import user_virtual_network as kbs_user_virtual_network, other
from src.crud.user import user_manager
from src.models.order import OrderStatus, OrderType
from src.schemas.order import CreateOrderSchema

loger = logging.getLogger(__name__)


router = Router()

status_virtual_network = {
    "active": "Активный",
    "disabled": "Неактивен",
    "expired": "Срок действия окончен",
    "limited": "Превышен лимит трафика",
}

multiplier_billing_period = {
    "day": 1,
    "month": 30,
    "year": 360,
}

billing_period = {
    "day": "день",
    "month": "мес",
    "year": "год",
}


@router.callback_query(
    F.data.in_(["my_virtual_network", "back_to_list_user_virtual_networks"])
)
async def view_user_virtual_networks(call: CallbackQuery, db_session: AsyncSession):
    user = await user_manager.get_user_virtual_network(
        session=db_session, id_=call.from_user.id
    )

    virtual_network_key = [
        virtual_network.virtual_network_key
        for virtual_network in user.user_virtual_networks
    ]
    await call.message.edit_text(
        text="Ключи, которые вы приобрели",
        reply_markup=kbs_user_virtual_network.list_user_virtual_networks_inline_buttons_builder(
            virtual_network_key
        ),
    )


@router.callback_query(F.data.startswith("extend_traffic"))
async def extend_virtual_network_traffic(
    call: CallbackQuery, db_session: AsyncSession, state: FSMContext
):
    virtual_network_key = call.data.split("-")[-1]
    await state.update_data(virtual_network_key=virtual_network_key)
    tariffs = await tariff_manager.get_tariffs(session=db_session)
    tariff_keys = [
        {
            "tariff_key": tariff.id,
            "traffic_limit": tariff.traffic_limit,
        }
        for tariff in tariffs
    ]
    await call.message.edit_text(
        text="На сколько расшить трафик",
        reply_markup=kbs_user_virtual_network.extend_virtual_network_traffic_inline_buttons_builder(
            tariffs=tariff_keys
        ),
    )


@router.callback_query(F.data.startswith("add_traffic"))
async def add_traffic_to_user_virtual_network(
    call: CallbackQuery, db_session: AsyncSession, state: FSMContext
):
    data = await state.get_data()
    tariff_id = call.data.split("-")[-1]
    tariff = await tariff_manager.get_active_tariff_by_id(
        session=db_session, tariff_id=int(tariff_id)
    )
    tg_user = await user_manager.get_by_tg_id(db_session, id_=call.from_user.id)

    order_schema = CreateOrderSchema(
        tariff_id=tariff.id,
        tg_user_id=tg_user.id,
        status=OrderStatus.start,
        type=OrderType.refill_traffic,
        currency=tariff.currency,
        amount=tariff.price,
    )
    order = await order_manager.create(
        session=db_session,
        obj_schema=order_schema,
    )
    order.virtual_network_key = data["virtual_network_key"]
    await state.clear()
    await call.message.edit_text(
        text=f"""
Информация о заказе: 
Цена - {order.tariff.view_price}
Количество пополняемого трафика- {order.tariff.traffic_limit}гб
            """,
        reply_markup=kbs_user_virtual_network.user_validate_extend_virtual_network_traffic_inline_buttons(
            user_id=call.from_user.id,
            order_id=order.id,
        ),
    )


@router.callback_query(F.data.startswith("user_approve_extend_virtual_network_traffic"))
async def user_approve_extend_virtual_network_traffic(
    call: CallbackQuery, db_session: AsyncSession
):
    _, _, order_id = call.data.split("-")
    order = await order_manager.get_by_id_with_tariff(
        session=db_session, id_=int(order_id)
    )
    order.status = OrderStatus.in_progress

    await call.message.edit_text(
        text="""
Реквизиты для оплаты.
Номер телефона: 89634008750 (Сбербанк)

После оплаты в чате будет выслан vpn ключ.
            """
    )
    for admin in bot_settings.ADMINS:
        await call.bot.send_message(
            chat_id=admin,
            text=f""" 
Пользователь {call.from_user.username}
сделал заказан на пополнение трафика.

Информация о заказе: 
Цена - {order.tariff.view_price}
Количество пополняемого трафика- {order.tariff.traffic_limit}гб
                                        """,
            reply_markup=kbs_user_virtual_network.admin_validate_extend_virtual_network_traffic_inline_buttons(
                user_id=call.from_user.id,
                order_id=order.id,
            ),
        )


@router.callback_query(F.data.startswith("user_cancel_extend_virtual_network_traffic"))
async def user_cancel_extend_virtual_network_traffic(
    call: CallbackQuery, state: FSMContext, db_session: AsyncSession
):
    await state.clear()
    _, _, order_id = call.data.split("-")
    order = await order_manager.get_by_id_with_tariff(
        session=db_session, id_=int(order_id)
    )
    order.status = OrderStatus.failed
    order.deleted_at = datetime.now()

    await call.message.edit_text(
        "Заказ отменен",
        reply_markup=other.move_to(
            text="🔙Назад", callback_data="back_to_list_user_virtual_networks"
        ),
    )


@router.callback_query(
    F.data.startswith("admin_approve_extend_virtual_network_traffic")
)
async def admin_approve_extend_virtual_network_traffic(
    call: CallbackQuery, db_session: AsyncSession
):
    _, user_id, order_id = call.data.split("-")

    order = await order_manager.get_by_id_with_tariff(
        session=db_session, id_=int(order_id)
    )
    order.status = OrderStatus.completed

    user_virtual_network = await user_virtual_networks_manager.get_user_virtual_network_by_virtual_network_key_with_marzban(
        session=db_session,
        virtual_network_key=order.virtual_network_key,
    )
    user_virtual_network.traffic_limit += order.tariff.traffic_limit
    r = await marzban_manager.update_traffic_to_marz_user(
        name_user_virtual_network=user_virtual_network.virtual_network_key,
        marzban_service_name=user_virtual_network.marzban_service.name,
        value=int(user_virtual_network.traffic_limit) * (1024**3),
    )
    if not r:
        await call.message.answer(text="Произошла ошибка")
    user_virtual_network.notified_low_traffic_data = False
    user_virtual_network.notified_traffic_data_done = False

    await call.message.edit_text(
        text=f"""
    {call.message.text}
    
    ОПАЛЧЕНО!!!
    """,
    )

    await call.bot.send_message(
        chat_id=user_id,
        text=f"""
Оплата прошла!!
            """,
    )


@router.callback_query(F.data.startswith("admin_cancel_extend_virtual_network_traffic"))
async def admin_cancel_extend_virtual_network_traffic(
    call: CallbackQuery, db_session: AsyncSession
):

    _, _, order_id = call.data.split("-")
    order = await order_manager.get_by_id(session=db_session, id_=int(order_id))
    order.status = OrderStatus.failed
    order.deleted_at = datetime.now()

    user_id = call.data.split("-")[-2]
    text = f"""
{call.message.text}

НЕОПЛАЧЕНО!!!
    """
    await call.message.edit_text(
        text=text,
    )
    await call.bot.send_message(
        chat_id=user_id,
        text="Оплата не пришла",
    )


@router.callback_query(F.data.startswith("delete_virtual_network"))
async def delete_virtual_network(
    call: CallbackQuery, state: FSMContext, db_session: AsyncSession
):
    await state.clear()
    virtual_network_key = call.data.split("-")[-1]
    user_virtual_network = await user_virtual_networks_manager.get_user_virtual_network_by_virtual_network_key_with_marzban(
        session=db_session,
        virtual_network_key=virtual_network_key,
    )
    user_virtual_network.deleted_at = datetime.now(timezone.utc)
    await marzban_manager.delete_user_virtual_network(
        name_user_virtual_network=virtual_network_key,
        marzban_service_name=user_virtual_network.marzban_service.name,
    )
    await call.message.edit_text(
        text="Виртуальная сеть была удалена",
        reply_markup=move_to(
            text="🔙Назад", callback_data="back_to_list_user_virtual_networks"
        ),
    )


@router.callback_query(F.data.startswith("extend_expire"))
async def extend_virtual_network_traffic(
    call: CallbackQuery, db_session: AsyncSession, state: FSMContext
):
    virtual_network_key = call.data.split("-")[-1]
    await state.update_data(virtual_network_key=virtual_network_key)
    tariffs = await tariff_manager.get_tariffs(session=db_session)
    tariff_keys = [
        {
            "tariff_key": f"add_time_to_expire-{tariff.id}",
            "traffic_limit": f"{tariff.term} {billing_period[tariff.billing_period.value]}",
        }
        for tariff in tariffs
    ]

    answer_text = "\n".join(
        [
            f"├  {tariff.term} {billing_period[tariff.billing_period.value]}: {tariff.view_price} (лимит - {tariff.traffic_limit}гб)"
            for tariff in tariffs
        ]
    )

    await call.message.edit_text(
        text=f"""
На сколько расшить трафик

{answer_text}
""",
        reply_markup=kbs_user_virtual_network.extend_virtual_network_expired_inline_buttons_builder(
            tariffs=tariff_keys
        ),
    )


@router.callback_query(F.data.startswith("add_time_to_expire"))
async def add_traffic_to_user_virtual_network(
    call: CallbackQuery, db_session: AsyncSession, state: FSMContext
):
    data = await state.get_data()
    _, tariff_id = call.data.split("-")
    tariff = await tariff_manager.get_active_tariff_by_id(
        session=db_session, tariff_id=int(tariff_id)
    )
    await call.message.answer("asdaws")

    tg_user = await user_manager.get_by_tg_id(db_session, id_=call.from_user.id)

    order_schema = CreateOrderSchema(
        tariff_id=tariff.id,
        tg_user_id=tg_user.id,
        status=OrderStatus.start,
        type=OrderType.refill_expire,
        currency=tariff.currency,
        amount=tariff.price,
    )
    order = await order_manager.create(
        session=db_session,
        obj_schema=order_schema,
    )
    order.virtual_network_key = data["virtual_network_key"]
    await state.clear()
    await call.message.edit_text(
        text=f"""
Информация о заказе:
Цена - {order.tariff.view_price}
На сколько продлить срок жизни токена- {order.tariff.term} {billing_period[order.tariff.billing_period.value]}
            """,
        reply_markup=kbs_user_virtual_network.user_validate_extend_virtual_network_expire_inline_buttons(
            user_id=call.from_user.id,
            order_id=order.id,
        ),
    )


@router.callback_query(F.data.startswith("user_approve_extend_virtual_network_expire"))
async def user_approve_extend_virtual_network_expire(
    call: CallbackQuery, db_session: AsyncSession
):
    _, _, order_id = call.data.split("-")
    order = await order_manager.get_by_id_with_tariff(
        session=db_session, id_=int(order_id)
    )
    order.status = OrderStatus.in_progress

    await call.message.edit_text(
        text="""
Реквизиты для оплаты.
Номер телефона: 89634008750 (Сбербанк)

После оплаты в чате будет выслан vpn ключ.
            """
    )
    for admin in bot_settings.ADMINS:
        await call.bot.send_message(
            chat_id=admin,
            text=f""" 
Пользователь {call.from_user.username}
сделал заказан на увеличение срока жизни.

Информация о заказе: 
Цена - {order.tariff.view_price}
На сколько увеличится срок жизни - {order.tariff.term} {billing_period[order.tariff.billing_period.value]}
                                        """,
            reply_markup=kbs_user_virtual_network.admin_validate_extend_virtual_network_expire_inline_buttons(
                user_id=call.from_user.id,
                order_id=order.id,
            ),
        )


@router.callback_query(F.data.startswith("user_cancel_extend_virtual_network_expire"))
async def user_cancel_extend_virtual_network_traffic(
    call: CallbackQuery, state: FSMContext, db_session: AsyncSession
):
    await state.clear()
    _, _, order_id = call.data.split("-")
    order = await order_manager.get_by_id_with_tariff(
        session=db_session, id_=int(order_id)
    )
    order.status = OrderStatus.failed
    order.deleted_at = datetime.now()

    await call.message.edit_text(
        "Заказ отменен",
        reply_markup=other.move_to(
            text="🔙Назад", callback_data="back_to_list_user_virtual_networks"
        ),
    )


@router.callback_query(F.data.startswith("admin_approve_extend_virtual_network_expire"))
async def admin_approve_extend_virtual_network_expire(
    call: CallbackQuery, db_session: AsyncSession
):
    _, user_id, order_id = call.data.split("-")

    order = await order_manager.get_by_id_with_tariff(
        session=db_session, id_=int(order_id)
    )
    order.status = OrderStatus.completed

    user_virtual_network = await user_virtual_networks_manager.get_user_virtual_network_by_virtual_network_key_with_marzban(
        session=db_session,
        virtual_network_key=order.virtual_network_key,
    )
    extend_expire = (
        order.tariff.term * multiplier_billing_period[order.tariff.billing_period.value]
    )
    user_virtual_network.expire += timedelta(days=extend_expire)
    user_virtual_network.used_traffic = 0
    r = await marzban_manager.update_expire_to_marz_user(
        name_user_virtual_network=user_virtual_network.virtual_network_key,
        marzban_service_name=user_virtual_network.marzban_service.name,
        extend_date_by=extend_expire,
    )
    if not r:
        await call.message.answer("Произошла ошибка")

    await marzban_manager.reset_virtual_network_data(
        name_user_virtual_network=user_virtual_network.virtual_network_key,
        tariff_id=order.tariff.id,
        marzban_service_name=user_virtual_network.marzban_service.name,
    )

    user_virtual_network.notified_expired_soon = False
    user_virtual_network.notified_expired_done = False

    await call.message.edit_text(
        text=f"""
    {call.message.text}

    ОПАЛЧЕНО!!!
    """,
    )

    await call.bot.send_message(
        chat_id=user_id,
        text=f"""
Оплата прошла!!
            """,
    )


@router.callback_query(F.data.startswith("admin_cancel_extend_virtual_network_expire"))
async def admin_cancel_extend_virtual_network_expire(
    call: CallbackQuery, db_session: AsyncSession
):
    order_id = call.data.split("-")[-1]
    order = await order_manager.get_by_id(session=db_session, id_=int(order_id))
    order.status = OrderStatus.failed
    order.deleted_at = datetime.now()

    user_id = call.data.split("-")[-2]
    text = f"""
{call.message.text}

НЕОПЛАЧЕНО!!!
    """
    await call.message.edit_text(
        text=text,
    )
    await call.bot.send_message(
        chat_id=user_id,
        text="Оплата не пришла",
    )


@router.callback_query(F.data.startswith("virtual_network-"))
async def view_user_virtual_networks(call: CallbackQuery, db_session: AsyncSession):
    virtual_network_key = call.data.split("-")[-1]
    user_virtual_network = await user_virtual_networks_manager.get_user_virtual_network_by_virtual_network_key_with_marzban(
        session=db_session, virtual_network_key=virtual_network_key
    )
    await call.message.edit_text(
        parse_mode=ParseMode.MARKDOWN,
        text=f"""
Статус: {EnumStatusVirtualNetwork[user_virtual_network.status.value].value}
Лимит трафика: {int(user_virtual_network.traffic_limit)} гб
Использовано трафика трафика: {user_virtual_network.used_traffic}

Срок окончания: {user_virtual_network.expire.strftime("%d.%m.%Y %H:%M")}


```
{user_virtual_network.virtual_networks}
```
        """,
        reply_markup=kbs_user_virtual_network.user_virtual_network_inline_buttons_builder(
            user_virtual_network_key=virtual_network_key
        ),
    )
