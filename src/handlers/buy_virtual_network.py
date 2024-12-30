import logging

from aiogram import Router, F
from aiogram.types import CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from src.kbs import buy_virtual_network as kbs_buy_virtual_network
from src.crud.price import country_manager

loger = logging.getLogger(__name__)


router = Router()

billing_period = {
    "day": "день",
    "month": "мес",
    "year": "год",
}


@router.callback_query(F.data.in_(["buy_virtual_network"]))
async def choice_virtual_network_county(call: CallbackQuery, db_session: AsyncSession):
    """Обработчик где выбирают страну"""
    counties = await country_manager.get_all(db_session)
    counties_data_list = [
        {"text": county.view_country, "callback_data": county.key_country}
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
