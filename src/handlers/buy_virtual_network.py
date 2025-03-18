import datetime
import logging

from aiogram import Router, F
from aiogram.enums import ParseMode
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from src.kbs.other import move_to
from src.crud.marzban import marzban_service_manager
from src.handlers.user_virtual_network import multiplier_billing_period
from src.kbs import buy_virtual_network as kbs_buy_virtual_network, other
from src.crud.virtual_network import (
    tariff_manager,
    user_virtual_networks_manager,
)
from src.crud.order import order_manager
from src.crud.user import user_manager, tg_user_order_message_manager
from src.models.order import OrderType, OrderStatus
from src.models.vpn import StatusVirtualNetwork, TypeVirtualNetwork
from src.schemas.order import CreateOrderSchema
from src.schemas.virtual_network import CreateUserVirtualNetworkSchema
from src.schemas.user import CreateTgUserOrderMessageSchema
from src.marzban.client import marzban_manager
from src.utils.generate_random import generate_random_string

loger = logging.getLogger(__name__)


router = Router()

billing_period = {
    "day": "день",
    "month": "мес",
    "year": "год",
}


@router.callback_query(F.data.in_(["buy_virtual_network"]))
async def tariff_list_handler(
    call: CallbackQuery, state: FSMContext, db_session: AsyncSession
):
    """Обработчик, который показывает все тарифы виртуальных сетей"""
    tariff_list = await tariff_manager.get_tariffs(db_session)
    data_tariff_list = [
        {
            "back_text": f"🎟️{tariff.view_price}",
            "back_callback_data": f"tariff-{tariff.id}",
        }
        for tariff in tariff_list
    ]
    answer_text = "\n".join(
        [
            f"├  {tariff.term} {billing_period[tariff.billing_period.value]}: {tariff.view_price} (лимит - {tariff.traffic_limit}гб)"
            for tariff in tariff_list
        ]
    )
    await call.message.edit_text(
        text=f"""
Лучшая сеть для анонимного сёрфинга в интернете!

{answer_text}
                """,
        reply_markup=kbs_buy_virtual_network.choice_tariffs_inline_buttons_builder(
            tariffs=data_tariff_list
        ),
    )


@router.callback_query(F.data.startswith("tariff-"))
async def choice_tariff_handler(call: CallbackQuery, db_session: AsyncSession):
    """
    Обработчик, который показывать информацию о выбранной виртуальной сети.
    Создается заказ на виртуальную сеть
    """
    tariff_id = call.data.split("-")[-1]
    tariff = await tariff_manager.get_active_tariff_by_id(db_session, int(tariff_id))
    tg_user = await user_manager.get_by_tg_id(db_session, id_=call.from_user.id)

    order_schema = CreateOrderSchema(
        tariff_id=tariff.id,
        tg_user_id=tg_user.id,
        status=OrderStatus.start,
        type=OrderType.buy,
        currency=tariff.currency,
        amount=tariff.price,
    )
    order = await order_manager.create(
        session=db_session,
        obj_schema=order_schema,
    )

    await call.message.edit_text(
        text=f"""
Информация о заказе:
Цена - {order.tariff.view_price}
Срок - {order.tariff.term} {billing_period[order.tariff.billing_period.value]}
Ограничение по трафику - {order.tariff.traffic_limit}гб
        """,
        reply_markup=kbs_buy_virtual_network.user_validate_buy_virtual_network_inline_buttons(
            user_id=call.from_user.id,
            order_id=order.id,
        ),
    )


@router.callback_query(F.data.startswith("user_approve_buy_virtual_network"))
async def user_approve_buy_virtual_network(
    call: CallbackQuery, db_session: AsyncSession
):
    """Обработчик, который срабатывает когда пользователь согласился с выбранным тарифом. В чат одмина поступит информация о заказа"""
    order_id = call.data.split("-")[-1]
    order = await order_manager.get_by_id_with_tariff(
        session=db_session, id_=int(order_id)
    )
    order.status = OrderStatus.in_progress

    await call.message.edit_text(
        text="""
Реквизиты для оплаты.
Номер телефона: 89634008750 (Сбербанк)

После оплаты в чате будет выслан ключ виртуальной сети.
            """
    )
    for admin in await user_manager.get_admins(db_session):
        msg = await call.bot.send_message(
            chat_id=admin,
            text=f""" 
Пользователь {call.from_user.username}
сделал заказан на покупки виртуальной сети.

Информация о заказе:
Цена - {order.tariff.view_price}
Срок - {order.tariff.term} {billing_period[order.tariff.billing_period.value]}
Ограничение по трафику - {order.tariff.traffic_limit}гб
                                        """,
            reply_markup=kbs_buy_virtual_network.admin_validate_buy_virtual_network_inline_buttons(
                user_id=call.from_user.id,
                order_id=order.id,
            ),
        )
        obj_schema = CreateTgUserOrderMessageSchema(
            tg_id=admin,
            order_id=order.id,
            message_id=msg.message_id,
        )
        await tg_user_order_message_manager.create(
            session=db_session, obj_schema=obj_schema
        )


@router.callback_query(F.data.startswith("user_cancel_buy_virtual_network"))
async def user_cancel_buy_virtual_network(
    call: CallbackQuery, state: FSMContext, db_session: AsyncSession
):
    """Обработчик, который срабатывает когда пользователь не согласился с выбранным тарифом. Тогда заказ отменяется"""
    await state.clear()
    order_id = call.data.split("-")[-1]
    order = await order_manager.get_by_id_with_tariff(
        session=db_session, id_=int(order_id)
    )
    order.status = OrderStatus.failed
    order.deleted_at = datetime.datetime.now()

    await call.message.edit_text(
        "Заказ отменен",
        reply_markup=other.move_to(text="🔙Назад", callback_data="back_to_start_menu"),
    )


@router.callback_query(F.data.startswith("admin_approve_buy_virtual_network"))
async def admin_approve_buy_virtual_network(
    call: CallbackQuery, state: FSMContext, db_session: AsyncSession
):
    """Обработчик, который срабатывает когда админ подтвердил приход средств оплаты после чего в чат покупателя приходит ключ виртуальной сети"""
    await state.clear()

    order_id = call.data.split("-")[-1]
    order = await order_manager.get_by_id_with_tariff(
        session=db_session, id_=int(order_id)
    )
    order.status = OrderStatus.completed

    user_id = call.data.split("-")[-2]
    user = await user_manager.get_by_tg_id(session=db_session, id_=int(user_id))

    virtual_network_key = f"{user.username}_{generate_random_string()}"
    order.virtual_network_key = virtual_network_key
    days_expire = (
        order.tariff.term * multiplier_billing_period[order.tariff.billing_period.value]
    )
    marzban_service = await marzban_service_manager.get_lower_count_users(
        session=db_session
    )
    expire = datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(
        days=days_expire
    )
    r = await marzban_manager.create_virtual_network(
        name_user_virtual_network=virtual_network_key,
        expire=expire,
        data_limit=order.tariff.traffic_limit * (1024**3),
        marzban_service_name=marzban_service.name,
    )
    if not r:
        await call.message.answer(text="Произошла ошибка")
    else:
        marzban_service.count_users += 1
        virtual_network = await marzban_manager.get_user_virtual_network_links(
            name_user_virtual_network=virtual_network_key,
            marzban_service_name=marzban_service.name,
        )

        user_virtual_network_schema = CreateUserVirtualNetworkSchema(
            virtual_network_key=virtual_network_key,
            status=StatusVirtualNetwork.active,
            type_virtual_networks=TypeVirtualNetwork.vless,
            virtual_networks=virtual_network["vless"],
            expire=expire,
            traffic_limit=order.tariff.traffic_limit,
            tg_user_id=user.id,
            marzban_service_id=marzban_service.id,
        )
        await user_virtual_networks_manager.create(
            session=db_session, obj_schema=user_virtual_network_schema
        )
        text = f"""
{call.message.text}
    
ОПАЛЧЕНО!!!

Заявку обработал {call.from_user.username}
"""
        massages = await tg_user_order_message_manager.get_by_order_id(
            session=db_session, order_id=order.id
        )
        for massages in massages:
            try:
                await call.bot.edit_message_text(
                    text=text,
                    chat_id=massages.tg_id,
                    message_id=massages.message_id,
                )
                massages.approve = True
                massages.tg_id_approve = call.from_user.id
            except TelegramBadRequest:
                pass

        await call.bot.send_message(
            chat_id=user_id,
            parse_mode=ParseMode.MARKDOWN,
            text=f"""
Приложение для ключа на IPhone | [V2rayTun](https://apps.apple.com/ru/app/v2raytun/id6476628951) <= нажать для установки
Приложение для ключа на Android | [v2rayNG](https://play.google.com/store/apps/details?id=com.v2ray.ang) <= нажать для установки

```
{virtual_network["vless"]}
```
            """,
            reply_markup=move_to(text="Назад 🔙", callback_data="back_to_start_menu"),
        )


@router.callback_query(F.data.startswith("admin_cancel_buy_virtual_network"))
async def admin_cancel_buy_virtual_network(
    call: CallbackQuery, state: FSMContext, db_session: AsyncSession
):
    """Обработчик, который срабатывает когда админ отклонил запрос так как оплата не пришла"""
    await state.clear()

    order_id = call.data.split("-")[-1]
    order = await order_manager.get_by_id(session=db_session, id_=int(order_id))
    order.status = OrderStatus.failed
    order.deleted_at = datetime.datetime.now()

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
