import datetime
import logging

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.settings import bot_settings
from src.kbs import buy_virtual_network as kbs_buy_virtual_network, other
from src.crud.price import country_manager, tariff_manager
from src.crud.order import order_manager
from src.crud.user import user_manager
from src.models.order import OrderType, OrderStatus
from src.schemas.order import CreateOrderSchema

loger = logging.getLogger(__name__)


router = Router()

billing_period = {
    "day": "день",
    "month": "мес",
    "year": "год",
}


@router.callback_query(F.data.in_(["buy_virtual_network", "back_to_choice_county"]))
async def choice_virtual_network_county(call: CallbackQuery, db_session: AsyncSession):
    """Обработчик где выбирают страну"""
    counties = await country_manager.get_all(db_session)
    counties_data_list = [
        {
            "text": county.view_country,
            "callback_data": f"{county.key_country}-{county.id}",
        }
        for county in counties
    ]
    await call.message.edit_text(
        text="""
Выберите страну для вашего VPN ⬇️\n
⚠️ Если вам нужен VPN для соцсетей или торрентов – вернитесь назад и выберите цель использования. Ни в коем случае не используйте просто страновой VPN для скачивания с торрентов!\n
⛔️ Выбирая страну самостоятельно, мы НЕ гарантируем что ваш инстаграм будет работать в России с российского IP 😄
        """,
        reply_markup=kbs_buy_virtual_network.choice_county_inline_buttons_builder(
            counties_data_list
        ),
    )


@router.callback_query(F.data.startswith("country-"))
async def country_price_list(
    call: CallbackQuery, state: FSMContext, db_session: AsyncSession
):
    """Обработчик, который показывает цены каждой страны"""
    country_id = call.data.split("-")[-1]
    country = await country_manager.get_by_id(db_session, country_id)
    tariff_list = await tariff_manager.get_country_tariff(db_session, country_id)
    data_price_list = [
        {
            "back_text": f"🎟️{tariff.view_price}",
            "back_callback_data": f"{tariff.tariff_key}",
        }
        for tariff in tariff_list
    ]
    answer_text = "\n".join(
        [
            f"├  {tariff.term} {billing_period[tariff.billing_period.value]}: {tariff.view_price} (лимит - {tariff.traffic_limit}гб)"
            for tariff in tariff_list
        ]
    )
    await state.update_data(country=country.view_country)
    await call.message.edit_text(
        text=f"""
{country.view_country}
💰 Лучший VPN по лучшей цене!

{answer_text}
                """,
        reply_markup=kbs_buy_virtual_network.choice_country_tariff_inline_buttons_builder(
            prices=data_price_list
        ),
    )


@router.callback_query(F.data.startswith("tariff-"))
async def choice_price_county(
    call: CallbackQuery, state: FSMContext, db_session: AsyncSession
):
    data = await state.get_data()
    tariff_key = call.data
    tariff = await tariff_manager.get_tariff_by_tariff_key(db_session, tariff_key)
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
Страна - {data['country']}
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
    call: CallbackQuery, state: FSMContext, db_session: AsyncSession
):
    data = await state.get_data()
    await state.clear()
    order_id = call.data.split("-")[-1]
    order = await order_manager.get_by_id_with_tariff(session=db_session, id_=order_id)
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
сделал заказан на впн.

Информация о заказе:
Страна - {data['country']}
Цена - {order.tariff.view_price}
Срок - {order.tariff.term} {billing_period[order.tariff.billing_period.value]}
Ограничение по трафику - {order.tariff.traffic_limit}гб
                                        """,
            reply_markup=kbs_buy_virtual_network.admin_validate_buy_virtual_network_inline_buttons(
                user_id=call.from_user.id,
                order_id=order.id,
            ),
        )


@router.callback_query(F.data.startswith("user_cancel_buy_virtual_network"))
async def user_cancel_buy_virtual_network(
    call: CallbackQuery, state: FSMContext, db_session: AsyncSession
):
    await state.clear()
    order_id = call.data.split("-")[-1]
    order = await order_manager.get_by_id_with_tariff(session=db_session, id_=order_id)
    order.status = OrderStatus.failed
    order.deleted_at = datetime.datetime.now()

    await call.message.edit_text(
        "Заказ отменен",
        reply_markup=other.move_to(text="🔙Назад", callback_data="back_to_start_menu"),
    )


@router.callback_query(F.data.startswith("admin_approve_buy_virtual_network"))
async def payment_receipt(
    call: CallbackQuery, state: FSMContext, db_session: AsyncSession
):
    await state.clear()

    order_id = call.data.split("-")[-1]
    order = await order_manager.get_by_id(session=db_session, id_=order_id)
    order.status = OrderStatus.completed

    user_id = call.data.split("-")[-2]
    text = f"""
{call.message.text}

ОПАЛЧЕНО!!!
"""
    await call.message.edit_text(
        text=text,
    )
    await call.bot.send_message(
        chat_id=user_id,
        text="Оплата прошла",
    )


@router.callback_query(F.data.startswith("admin_cancel_buy_virtual_network"))
async def payment_receipt(
    call: CallbackQuery, state: FSMContext, db_session: AsyncSession
):
    await state.clear()

    order_id = call.data.split("-")[-1]
    order = await order_manager.get_by_id(session=db_session, id_=order_id)
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
