import logging

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from src.core.settings import bot_settings
from src.kbs import buy_virtual_network as kbs_buy_virtual_network
from src.crud.price import country_manager, price_manager
from src.crud.order import order_manager, order_receipt_manger
from src.crud.user import user_manager
from src.models.order import OrderReceiptStatus
from src.schemas.order import CreateOrderSchema, CreateOrderReceiptSchema

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
    price_list = await price_manager.get_country_price(db_session, country_id)
    data_price_list = [
        {
            "back_text": f"🎟️{price.view_price}",
            "back_callback_data": f"{price.price_key}",
        }
        for price in price_list
    ]
    answer_text = "\n".join(
        [
            f"├  {price.term} {billing_period[price.billing_period.value]}: {price.view_price} (лимит - {price.traffic_limit}гб)"
            for price in price_list
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


@router.callback_query(F.data.startswith("tariff_"))
async def choice_price_county(
    call: CallbackQuery, state: FSMContext, db_session: AsyncSession
):
    data = await state.get_data()
    price_key = call.data
    price = await price_manager.get_price_by_price_key(db_session, price_key)
    tg_user = await user_manager.get_by_tg_id(db_session, id_=call.from_user.id)

    order_schema = CreateOrderSchema(
        price_id=price.id, tg_user_id=tg_user.id, status=True
    )
    order = await order_manager.create(
        session=db_session,
        obj_schema=order_schema,
    )

    order_receipt_schema = CreateOrderReceiptSchema(
        order_id=order.id,
        currency=price.currency,
        status=OrderReceiptStatus.in_progress,
        amount=price.price,
    )
    order_receipt = await order_receipt_manger.create(
        session=db_session,
        obj_schema=order_receipt_schema,
    )
    await call.message.edit_text(
        text=f"""
Ваш заказ был принят✅

Информация о заказе:
Страна - {data['country']}
Цена - {order.price.view_price}
Срок - {order.price.term} {billing_period[order.price.billing_period.value]}
Ограничение по трафику - {order.price.traffic_limit}гб

        """
    )
    await call.message.answer(
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
Пользователь {order.tg_user.username}
сделал заказан на впн.


Информация о заказе:
Страна - {data['country']}
Цена - {order.price.view_price}
Срок - {order.price.term} {billing_period[order.price.billing_period.value]}
Ограничение по трафику - {order.price.traffic_limit}гб
                                    """,
            reply_markup=kbs_buy_virtual_network.validate_buy_virtual_network_inline_buttons(
                user_id=order.tg_user.tg_id,
                order_receipt_id=order_receipt.id,
            ),
        )


@router.callback_query(F.data.startswith("approve_buy_virtual_network"))
async def payment_receipt(
    call: CallbackQuery, state: FSMContext, db_session: AsyncSession
):
    await state.clear()

    order_receipt_id = call.data.split("-")[-1]
    order_receipt = await order_receipt_manger.get_by_id(
        session=db_session, id_=order_receipt_id
    )
    order_receipt.status = OrderReceiptStatus.completed

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


@router.callback_query(F.data.startswith("cancel_buy_virtual_network"))
async def payment_receipt(
    call: CallbackQuery, state: FSMContext, db_session: AsyncSession
):
    await state.clear()

    order_receipt_id = call.data.split("-")[-1]
    order_receipt = await order_receipt_manger.get_by_id(
        session=db_session, id_=order_receipt_id
    )
    order_receipt.status = OrderReceiptStatus.failed

    order = await order_manager.get_by_id(
        session=db_session, id_=order_receipt.order_id
    )
    order.status = False

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
