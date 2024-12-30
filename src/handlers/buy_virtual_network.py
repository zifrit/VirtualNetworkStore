import logging

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from src.kbs import buy_virtual_network as kbs_buy_virtual_network
from src.crud.price import country_manager, price_manager

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
