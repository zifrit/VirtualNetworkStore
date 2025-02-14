import logging

from aiogram import Router, F
from aiogram.types import CallbackQuery
from aiogram.utils.deep_linking import create_start_link

loger = logging.getLogger(__name__)


router = Router()


@router.callback_query(F.data == "partners")
async def start_command(call: CallbackQuery):
    user_id = call.from_user.id
    link = await create_start_link(call.message.bot, str(user_id), encode=True)

    await call.message.edit_text(f"Ваша реферальная ссылка: {link}")
