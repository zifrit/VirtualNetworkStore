import logging
from aiogram import Router, F
from aiogram.filters import CommandStart, CommandObject
from aiogram.utils.deep_linking import decode_payload
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession
from src.utils.check_sub import check_subscription
from src.crud.user import user_manager, referral_manager
from src.schemas.user import CreateTgUserSchema, CreateReferralSchema
from src.kbs import user as kbs_user


loger = logging.getLogger("admin_log")


router = Router()


@router.message(CommandStart())
async def start_handler(
    message: Message, command: CommandObject, db_session: AsyncSession
):
    """Стартовая обработчик который приветствует, создает пользователя и проверяет рефералку"""
    if await check_subscription(message.from_user.id, message.bot):
        if not await user_manager.get_by_tg_id(db_session, message.from_user.id):
            create_user = CreateTgUserSchema(
                username=(
                    message.from_user.username
                    if message.from_user.username
                    else message.from_user.id
                ),
                tg_id=message.from_user.id,
            )
            await user_manager.create(
                db_session,
                obj_schema=create_user,
            )
            loger.info("Пользователь %s был создан базе данных", message.from_user.id)
        if command.args is not None:
            loger.info(
                "Пользователь %s перешел по ссылке %s к боту",
                message.from_user.id,
                int(decode_payload(command.args)),
            )
            if message.from_user.id != int(decode_payload(command.args)):
                create_referral = CreateReferralSchema(
                    referrer_tg_id=message.from_user.id,
                    referred_tg_id=int(decode_payload(command.args)),
                )
                status = await referral_manager.create(
                    session=db_session,
                    obj_schema=create_referral,
                )
                if status:
                    await message.answer(
                        "Рефиралка принята",
                    )
                else:
                    await message.answer(
                        "Уже есть рефиралка",
                    )
        await message.answer(
            """
Шмель-VPN🐝: Летим без ограничений! Привет, друзья!
Шмель-VPN – это ваш надежный спутник в мире без ограничений! Безлимитный трафик, никаких замедлений скорости – просто летите, куда хотите!
Все ваши любимые соцсети работают без сбоев, а выбор стран – на любой вкус!  Летим вместе с Шмель-VPN!
        """,
            reply_markup=kbs_user.start_inline_button,
        )
    else:
        await message.answer("Вы не подписались на канал https://t.me/shmel_x!!")


@router.callback_query(F.data == "back_to_start_menu")
async def start_handler(call: CallbackQuery):
    await call.message.edit_text(
        """
Шмель-VPN🐝: Летим без ограничений!
Привет, друзья! Шмель-VPN – это ваш надежный спутник в мире без ограничений! Безлимитный трафик, никаких замедлений скорости – просто летите, куда хотите! 
Все ваши любимые соцсети работают без сбоев, а выбор стран – на любой вкус!  Летим вместе с Шмель-VPN!
    """,
        reply_markup=kbs_user.start_inline_button,
    )
