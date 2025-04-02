import logging
from aiogram import Router, F
from aiogram.filters import CommandStart, CommandObject
from aiogram.utils.deep_linking import decode_payload
from aiogram.types import Message, CallbackQuery
from sqlalchemy.ext.asyncio import AsyncSession

from src.kbs.help import help_inline
from src.kbs.other import move_to
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
Шмель🐝: Летим без ограничений!
Привет, друзья! Шмель – это ваш надежный спутник в мире без ограничений! Безлимитный трафик, никаких замедлений скорости – просто летите, куда хотите! 
Все ваши любимые соцсети работают без сбоев, а выбор стран – на любой вкус!  Летим вместе с Шмель!
        """,
            reply_markup=kbs_user.start_inline_button,
        )
    else:
        await message.answer(
            """
✨ Добро пожаловать!

Для доступа к функциям бота, пожалуйста, подпишитесь на наш официальный канал:https://t.me/shmel_x

📌 Важное напоминание:
После подписки на канал вернитесь в бота и нажмите кнопку  “Меню” потом запустить бота, чтобы получить доступ к функциям!

🔄 Это необходимо для обновления данных о вашей подписке.

Приятного использования! 🚀
        """
        )


@router.callback_query(F.data == "back_to_start_menu")
async def start_handler(call: CallbackQuery):
    await call.message.edit_text(
        """
Шмель🐝: Летим без ограничений!
Привет, друзья! Шмель – это ваш надежный спутник в мире без ограничений! Безлимитный трафик, никаких замедлений скорости – просто летите, куда хотите! 
Все ваши любимые соцсети работают без сбоев, а выбор стран – на любой вкус!  Летим вместе с Шмель!
    """,
        reply_markup=kbs_user.start_inline_button,
    )


@router.callback_query(F.data == "user_help")
async def start_handler(call: CallbackQuery):
    s = "Назат"
    await call.message.edit_text(
        """
🔧 Помощь

Основные причины проблем с подключением и их решения:

Проблемы с приложением:
• Перезагрузите телефон
• Проверьте подключение к интернету
• Включите и выключите режим полета
• Очистите кэш приложения
• Переустановите приложения
Технические вопросы:
• Проверьте, не используете ли вы общедоступный Wi-Fi
Если проблема остается, обращайтесь к администратору:
Ник: @Mishka0777

При обращении укажите:

Описание проблемы
Что вы пробовали сделать
Скриншот ошибки (если есть)
Мы поможем решить вашу проблему! 🎯
    """,
        reply_markup=help_inline,
    )


@router.callback_query(F.data == "about_us")
async def start_handler(call: CallbackQuery):
    await call.message.edit_text(
        """
🎯 О НАС
Мы предоставляем услуги для безопасного сёрфинга в интернете. Наша команда профессионалов заботится о твоей конфиденциальности и комфорте.

📱 ПОДДЕРЖКА
Возникли вопросы или проблемы? Пиши нам: @mishka0777

При обращении укажите:
• Модель телефона
• Версию приложения
• Описание проблемы
• Скриншот (если возможно)

Работаем для вас 24/7! 
этот текст в кнопку помощь
    """,
        reply_markup=move_to(text="Назад 🔙", callback_data="back_to_start_menu"),
    )
