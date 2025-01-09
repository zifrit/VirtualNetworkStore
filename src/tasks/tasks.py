import logging
from datetime import datetime, timedelta

from src.tasks.celery import celery_app
from src.core.db_connections import db_session
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from src.models.vpn import UserVirtualNetworks
from src.models.user import TgUser
from src.marzban.client import marzban_manager
from src.core.settings import bot
import asyncio

loger = logging.getLogger("admin_log")


async def check_user_virtual_network_traffic():
    async with db_session.session_factory() as session:
        user_virtual_networks = await session.scalars(
            select(UserVirtualNetworks)
            .options(
                joinedload(UserVirtualNetworks.tg_user).load_only(
                    TgUser.tg_id,
                    TgUser.id,
                    TgUser.username,
                )
            )
            .where(UserVirtualNetworks.deleted_at.is_(None))
        )
        for user_virtual_network in user_virtual_networks:  # type: UserVirtualNetworks
            virtual_network = await marzban_manager.get_marz_user_virtual_network(
                name_user_virtual_network=user_virtual_network.virtual_network_key
            )
            if virtual_network.data_limit < virtual_network.used_traffic:
                await bot.send_message(
                    chat_id=user_virtual_network.tg_user.tg_id,
                    text="У вас закончился трафика, советую вас пополнить количество гигабайт",
                )
                user_virtual_network.notified_traffic_data_done = True
                loger.info(
                    "У пользователя %s у ключа %s скоро закончится трафик",
                    user_virtual_network.tg_user.tg_id,
                    user_virtual_network.virtual_network_key,
                )
            elif virtual_network.data_limit - virtual_network.used_traffic < 5:
                await bot.send_message(
                    chat_id=user_virtual_network.tg_user.tg_id,
                    text="У вас скоро закончится количество трафика, советую вас пополнить количество гигабайт",
                )
                user_virtual_network.notified_low_traffic_data = True
                loger.info(
                    "У пользователя %s у ключа %s закончился трафик",
                    user_virtual_network.tg_user.tg_id,
                    user_virtual_network.virtual_network_key,
                )
        await session.commit()


async def check_user_virtual_network_expired():
    async with db_session.session_factory() as session:
        user_virtual_networks = await session.scalars(
            select(UserVirtualNetworks)
            .options(
                joinedload(UserVirtualNetworks.tg_user).load_only(
                    TgUser.tg_id,
                    TgUser.id,
                    TgUser.username,
                )
            )
            .where(UserVirtualNetworks.deleted_at.is_(None))
        )
        for user_virtual_network in user_virtual_networks:  # type: UserVirtualNetworks
            virtual_network = await marzban_manager.get_marz_user_virtual_network(
                name_user_virtual_network=user_virtual_network.virtual_network_key
            )

            date_now = datetime.now()
            virtual_network_expire_date = datetime.fromtimestamp(virtual_network.expire)
            must_more = timedelta(days=1)
            if date_now - virtual_network_expire_date < must_more:
                await bot.send_message(
                    chat_id=user_virtual_network.tg_user.tg_id,
                    text=f"Срок жизни вашего ключа {user_virtual_network.virtual_network_key} скоро закончится",
                )
                user_virtual_network.notified_expired_soon = True
                loger.info(
                    "У пользователя %s скоро закончится срок жизни ключа %s",
                    user_virtual_network.tg_user.tg_id,
                    user_virtual_network.virtual_network_key,
                )
            elif (date_now - virtual_network_expire_date).total_seconds() < 0:
                await bot.send_message(
                    chat_id=user_virtual_network.tg_user.tg_id,
                    text=f"Срок жизни вашего ключа {user_virtual_network.virtual_network_key} закончился",
                )
                user_virtual_network.notified_expired_done = True
                loger.info(
                    "У пользователя %s закончился срок жизни ключа %s",
                    user_virtual_network.tg_user.tg_id,
                    user_virtual_network.virtual_network_key,
                )
        await session.commit()


@celery_app.task
def task_check_user_virtual_network_traffic():
    asyncio.run(check_user_virtual_network_traffic())


@celery_app.task
def task_check_user_virtual_network_expired():
    asyncio.run(check_user_virtual_network_expired())
