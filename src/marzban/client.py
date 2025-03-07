import asyncio
import logging
from datetime import datetime, timedelta, timezone
from logging import Logger
from typing import Optional

import httpx
from marzban_api_client import AuthenticatedClient, Client
from marzban_api_client.api.admin import admin_token
from marzban_api_client.models.body_admin_token_api_admin_token_post import (
    BodyAdminTokenApiAdminTokenPost,
)
from marzban_api_client.api.user import (
    add_user,
    get_user,
    modify_user,
    delete_expired_users,
    reset_user_data_usage,
    get_users,
)
from marzban_api_client.models import (
    UserCreate,
    UserCreateProxies,
    UserResponse,
    UserModify,
    UserDataLimitResetStrategy,
)
from marzban_api_client.types import Response

from core.db_connections import db_session
from crud.virtual_network import tariff_manager
from src.core.settings import marzban_settings


logger = logging.getLogger(__name__)
admin_logger = logging.getLogger("admin_log")


class MarzBanClient:
    def __init__(self, base_url: str, logger: Logger):
        self._client: Optional[AuthenticatedClient] = None
        self._exp_at: Optional[datetime] = None
        self._base_url: str = base_url
        self._logger = logger
        self._token: str = ""

    async def get_client(self) -> AuthenticatedClient:
        """
        Получение клиента для работы с системой
        :return:
        """
        if not self._client or self._exp_at < datetime.now():
            self._logger.info(f"Get new token")
            token = await self.get_token()
            self._token = token
            self._exp_at = datetime.now() + timedelta(minutes=1440)
            self._client = AuthenticatedClient(
                base_url=self._base_url, token=self._token, verify_ssl=True
            )
            self._logger.info(f"Set new client object")
        self._logger.info(f"We have client object")
        return self._client

    async def get_token(self) -> str:
        """
        Осуществляется вход в систему и получается токен для дальнейшей работы с клиентом
        :return:
        """
        try:
            login_data = BodyAdminTokenApiAdminTokenPost(
                username=marzban_settings.USERNAME,
                password=marzban_settings.PASSWORD,
            )
            async with Client(base_url=self._base_url) as client:
                token = await admin_token.asyncio(
                    client=client,
                    body=login_data,
                )
                access_token = token.access_token
                return access_token
        except Exception as e:
            self._logger.error(f"Error getting token: {e}")
            raise


class MarzBanManager:
    def __init__(self, logger: Logger, client: MarzBanClient):
        self._client: MarzBanClient = client
        self._logger: Logger = logger
        self._proxies: UserCreateProxies = UserCreateProxies.from_dict(
            {"vless": {"flow": "xtls-rprx-vision"}}
        )

    @property
    async def _db_client(self):
        async with db_session.session_factory() as session:
            try:
                return session
            except Exception as e:
                await session.rollback()
            finally:
                await session.close()

    async def create_virtual_network(
        self,
        name_user_virtual_network: str,
        expire,
        data_limit: int = 200,
    ) -> Response | bool:
        """
        Создание пользователя виртуальной сети в системе.
        :param name_user_virtual_network: Принимает название для пользователя виртуальной сети,
        :param expire: Время работы виртуальной сети,
        :param data_limit: Ограничение трафика для виртуальной сеит
        """
        exp_timestamp = MarzBanManager.expire_timestamp(expire)
        user_data = UserCreate(
            username=name_user_virtual_network,
            expire=exp_timestamp,
            proxies=self._proxies,
            data_limit=data_limit,
            data_limit_reset_strategy=UserDataLimitResetStrategy.NO_RESET,
        )
        try:
            response: Response = add_user.sync_detailed(
                client=await self._client.get_client(), body=user_data
            )
            self._logger.info(
                "Created %s virtual network. Status code %s",
                name_user_virtual_network,
                response.status_code,
            )
            return response.parsed
        except httpx.RequestError as e:
            self._logger.error("When update_traffic_to_marz_user happened error: %s", e)
            return False

    async def get_marz_user_virtual_network(
        self, name_user_virtual_network: str
    ) -> UserResponse | bool:
        """
        Получает пользователя виртуальной сети из системы
        :param name_user_virtual_network: Название пользователя виртуальной сети.
        """
        try:
            response: Response = await get_user.asyncio_detailed(
                name_user_virtual_network, client=await self._client.get_client()
            )
            self._logger.info(
                "Get '%s' virtual network data. Status code %s",
                name_user_virtual_network,
                response.status_code,
            )
            return response.parsed
        except httpx.RequestError as e:
            self._logger.error("When update_traffic_to_marz_user happened error: %s", e)
            return False

    async def update_traffic_to_marz_user(
        self, name_user_virtual_network: str, value: int
    ) -> Response | bool:
        """
        Расширяет лимит трафика пользователя виртуальной сети
        :param name_user_virtual_network:  Название пользователя виртуальной сети.
        :param value: Новое значение лимита
        """
        user_data = UserModify(
            data_limit=value,
        )
        try:
            response: Response = await modify_user.asyncio_detailed(
                name_user_virtual_network,
                client=await self._client.get_client(),
                body=user_data,
            )
            self._logger.info(
                "Virtual network '%s' set %s data limit",
                name_user_virtual_network,
                value,
            )
            return response.parsed
        except httpx.RequestError as e:
            self._logger.error("When update_traffic_to_marz_user happened error: %s", e)
            return False

    async def update_expire_to_marz_user(
        self, name_user_virtual_network: str, extend_date_by: int
    ) -> Response | bool:
        """
        Расширяет срок жизни пользователя виртуальной сети
        :param name_user_virtual_network:  Название пользователя виртуальной сети.
        :param extend_date_by: На сколько расширится срок жизни виртуальной сети
        """
        user_virtual_network = await self.get_marz_user_virtual_network(
            name_user_virtual_network=name_user_virtual_network
        )
        if not user_virtual_network:
            return False

        old_expire = datetime.fromtimestamp(user_virtual_network.expire)

        new_expire = MarzBanManager.expire_timestamp(
            old_expire + timedelta(days=extend_date_by)
        )
        user_data = UserModify(expire=new_expire)
        try:
            response: Response = await modify_user.asyncio_detailed(
                name_user_virtual_network,
                client=await self._client.get_client(),
                body=user_data,
            )
            self._logger.info(
                "Virtual network '%s' extended expire to %s ",
                name_user_virtual_network,
                old_expire + timedelta(days=extend_date_by),
            )
            return response.parsed
        except httpx.ReadError as e:
            self._logger.error("When update_expire_to_marz_user happened error: %s", e)
            return False

    async def get_user_virtual_network_links(
        self, name_user_virtual_network: str
    ) -> dict[str, str] | bool:
        """
        Получает все ключи для подключения к виртуальной сети.
        :param name_user_virtual_network: Название пользователя виртуальной сети.
        :return: Строка содержащая ключи подключения к виртуальной сети.
        """
        try:
            response: UserResponse = await self.get_marz_user_virtual_network(
                name_user_virtual_network
            )
        except httpx.ReadError as e:
            self._logger.error(
                "When get_user_virtual_network_links happened error: %s", e
            )
            return False
        keys = {}
        for link in response.links:
            key_data = link.split("://")
            if key_data[0] == "vmess":
                keys["vmess"] = link
            elif (key_data[0] == "vless") or (key_data[0] == "trojan"):
                if key_data[0] == "vless":
                    keys["vless"] = link
                if key_data[0] == "trojan":
                    keys["trojan"] = link
            elif key_data[0] == "ss":
                keys["shadowsocks"] = link
        self._logger.info(
            "Get '%s' Virtual network links: %s", name_user_virtual_network, keys
        )
        return keys

    async def delete_user_virtual_network(self, name_user_virtual_network: str) -> None:
        """
        Удаляет виртуальную сеть пользователя, уменьшая его срок жизни на 10 дней после чего удаляю всех у кого больше 10 как истек строк жизни.
        :param name_user_virtual_network: Название пользователя виртуальной сети.
        :return: None
        """
        thirty_days = MarzBanManager.expire_timestamp(
            datetime.now(timezone.utc) - timedelta(days=10)
        )
        user_data = UserModify(expire=thirty_days)
        await modify_user.asyncio_detailed(
            name_user_virtual_network,
            client=await self._client.get_client(),
            body=user_data,
        )

        delete_utc_time = datetime.now(timezone.utc) - timedelta(days=9, hours=23)
        await delete_expired_users.asyncio_detailed(
            expired_before=delete_utc_time, client=await self._client.get_client()
        )
        self._logger.info("Virtual network '%s' deleted", name_user_virtual_network)

    async def reset_user_virtual_network_data_usage(
        self, name_user_virtual_network: str
    ) -> None:
        """
        Сбрасывает количество потраченного трафика у виртуальной сети пользователя.
        :param name_user_virtual_network: Название пользователя виртуальной сети.
        :return: None
        """

        await reset_user_data_usage.asyncio_detailed(
            client=await self._client.get_client(), username=name_user_virtual_network
        )
        self._logger.info(
            "Virtual network '%s' reset traffic data", name_user_virtual_network
        )

    async def reset_virtual_network_data(
        self,
        name_user_virtual_network: str,
        tariff_id: int,
    ) -> None:
        """

        :param name_user_virtual_network: Название пользователя виртуальной сети.
        :param tariff_id: Идентификатор тарифа
        :return:
        """
        await self.reset_user_virtual_network_data_usage(
            name_user_virtual_network=name_user_virtual_network
        )
        session = await self._db_client
        tariff = await tariff_manager.get_active_tariff_by_id(
            tariff_id=tariff_id, session=session
        )

        await self.update_traffic_to_marz_user(
            name_user_virtual_network=name_user_virtual_network,
            value=tariff.traffic_limit,
        )

    async def ping(self) -> None:
        """
        Делает запрос на получения всех пользователей, сейчас выступает в роли проверки доступа к серверу
        :return:
        """
        response: Response = await get_users.asyncio_detailed(
            client=await self._client.get_client()
        )
        if response.status_code == 200:
            self._logger.info("Sever is work, code: %s", response.status_code)
        else:
            self._logger.error(
                "Server returned unexpected status code: %s", response.status_code
            )
        return response.parsed

    @staticmethod
    def expire_timestamp(expire: datetime):
        """Конвертация даты"""
        new_utc_timestamp = int(expire.timestamp())
        return new_utc_timestamp


marzban_client = MarzBanClient(marzban_settings.URL, logger=logger)
marzban_manager = MarzBanManager(admin_logger, marzban_client)


async def main():
    ...
    # data = await marzban_manager.get_user_virtual_network_links(
    #     name_user_virtual_network="zifrit-WwthmMFc"
    # )

    # expire = datetime.now(timezone.utc) + timedelta(days=1)
    #
    # await marzban_manager.create_virtual_network(
    #     name_user_virtual_network="test_1", expire=expire
    # )
    # await marzban_manager.add_traffic_to_marz_user(
    #     name_user_virtual_network="test_1", value=300
    # )
    # await marzban_manager.create_virtual_network(
    #     name_user_virtual_network="test_2", expire=expire
    # )

    # expire_1 = datetime.now(timezone.utc) - timedelta(days=2)
    # expire_2 = datetime.now(timezone.utc) - timedelta(days=6)
    #

    #
    # await marzban_manager.add_traffic_to_marz_user(
    #     name_user_virtual_network="test_2", value=300, expire=expire_2
    # )

    # await marzban_manager.delete_user_virtual_network("zifrit_2Em7oZsL")


if __name__ == "__main__":
    asyncio.run(main())
