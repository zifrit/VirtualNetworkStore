import logging

from aiogram import Router, F
from aiogram.types import CallbackQuery
from src.kbs.other import move_to

loger = logging.getLogger(__name__)


router = Router()


@router.callback_query(F.data.in_(["account"]))
async def user_account(call: CallbackQuery):
    """Обработчик кнопки "Аккаунт" где выводится информация о пользователе. Пока что только id"""
    await call.message.edit_text(
        text=f"""
Личный кабинет

🆔:{call.from_user.id}
        """,
        reply_markup=move_to(text="🔙Назад", callback_data="back_to_start_menu"),
    )
