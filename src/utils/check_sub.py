from aiogram.enums import ChatMemberStatus
from aiogram import Bot


async def check_subscription(user_id: int, bot: Bot) -> bool:
    """
    Проверка, подписан ли пользователь на канал.
    Возвращает True, если подписан, иначе False.
    """
    group = "-4598435557"
    chanel = "@test_chanel_2366654323"
    try:
        chat_member = await bot.get_chat_member(chat_id=group, user_id=user_id)
        return chat_member.status in [
            ChatMemberStatus.MEMBER,
            ChatMemberStatus.CREATOR,
            ChatMemberStatus.ADMINISTRATOR,
        ]
    except Exception:
        return False
