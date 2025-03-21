import logging
from datetime import datetime, timedelta

from src.core.db_connections import db_session
from sqlalchemy import select, and_, or_
from sqlalchemy.orm import joinedload
from src.models.vpn import UserVirtualNetworks
from src.models.user import TgUser
from src.models.marzban import MarzbanService
from src.marzban.client import marzban_manager
from src.core.settings import bot
from src.kbs.other import move_to

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
                ),
                joinedload(UserVirtualNetworks.marzban_service).load_only(
                    MarzbanService.id,
                    MarzbanService.name,
                ),
            )
            .where(
                and_(
                    UserVirtualNetworks.deleted_at.is_(None),
                    or_(
                        UserVirtualNetworks.notified_traffic_data_done.is_(False),
                        UserVirtualNetworks.notified_low_traffic_data.is_(False),
                    ),
                )
            )
        )
        for user_virtual_network in user_virtual_networks:  # type: UserVirtualNetworks
            virtual_network = await marzban_manager.get_marz_user_virtual_network(
                name_user_virtual_network=user_virtual_network.virtual_network_key,
                marzban_service_name=user_virtual_network.marzban_service.name,
            )
            if not virtual_network:
                return
            elif virtual_network.data_limit < virtual_network.used_traffic:
                await bot.send_message(
                    chat_id=user_virtual_network.tg_user.tg_id,
                    text="У вас закончился трафика, советую вас пополнить количество гигабайт",
                    reply_markup=move_to(
                        text="Пополнить трафик",
                        callback_data=f"extend_traffic-{user_virtual_network.virtual_network_key}",
                    ),
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
                    reply_markup=move_to(
                        text="Пополнить трафик",
                        callback_data=f"extend_traffic-{user_virtual_network.virtual_network_key}",
                    ),
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
        loger.info("task running")
        user_virtual_networks = await session.scalars(
            select(UserVirtualNetworks)
            .options(
                joinedload(UserVirtualNetworks.tg_user).load_only(
                    TgUser.tg_id,
                    TgUser.id,
                    TgUser.username,
                ),
                joinedload(UserVirtualNetworks.marzban_service).load_only(
                    MarzbanService.id,
                    MarzbanService.name,
                ),
            )
            .where(
                and_(
                    UserVirtualNetworks.deleted_at.is_(None),
                    or_(
                        UserVirtualNetworks.notified_expired_done.is_(False),
                        UserVirtualNetworks.notified_expired_soon.is_(False),
                    ),
                )
            )
        )
        for user_virtual_network in user_virtual_networks:  # type: UserVirtualNetworks
            virtual_network = await marzban_manager.get_marz_user_virtual_network(
                name_user_virtual_network=user_virtual_network.virtual_network_key,
                marzban_service_name=user_virtual_network.marzban_service.name,
            )
            if not virtual_network:
                return
            date_now = datetime.now()
            virtual_network_expire_date = datetime.fromtimestamp(virtual_network.expire)
            must_more = timedelta(days=1)
            if (virtual_network_expire_date - date_now).total_seconds() < 0:
                await bot.send_message(
                    chat_id=user_virtual_network.tg_user.tg_id,
                    text=f"Срок жизни вашего ключа {user_virtual_network.virtual_network_key} закончился",
                    reply_markup=move_to(
                        text="Продлить",
                        callback_data=f"extend_expire-{user_virtual_network.virtual_network_key}",
                    ),
                )
                user_virtual_network.notified_expired_done = True
                loger.info(
                    "У пользователя %s закончился срок жизни ключа %s",
                    user_virtual_network.tg_user.tg_id,
                    user_virtual_network.virtual_network_key,
                )
            elif virtual_network_expire_date - date_now < must_more:
                await bot.send_message(
                    chat_id=user_virtual_network.tg_user.tg_id,
                    text=f"Срок жизни вашего ключа {user_virtual_network.virtual_network_key} скоро закончится",
                    reply_markup=move_to(
                        text="Продлить",
                        callback_data=f"extend_expire-{user_virtual_network.virtual_network_key}",
                    ),
                )
                user_virtual_network.notified_expired_soon = True
                loger.info(
                    "У пользователя %s скоро закончится срок жизни ключа %s",
                    user_virtual_network.tg_user.tg_id,
                    user_virtual_network.virtual_network_key,
                )
        await session.commit()


async def ping_server():
    await marzban_manager.ping()
