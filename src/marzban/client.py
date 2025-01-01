import asyncio
import logging
import base64
import json
from datetime import datetime, timedelta
from logging import Logger
from typing import Optional
from urllib.parse import urlparse, parse_qs
from marzban_api_client import AuthenticatedClient, Client
from marzban_api_client.api.admin import admin_token
from marzban_api_client.models.body_admin_token_api_admin_token_post import (
    BodyAdminTokenApiAdminTokenPost,
)
from marzban_api_client.api.user import (
    add_user,
    get_user,
    modify_user,
)
from marzban_api_client.models import (
    UserCreate,
    UserCreateProxies,
    UserResponse,
    UserModify,
    UserDataLimitResetStrategy,
)
from marzban_api_client.types import Response
from src.core.settings import marzban_settings


logger = logging.getLogger(__name__)


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
        response: Response = add_user.sync_detailed(
            client=await self._client.get_client(), body=user_data
        )
        self._logger.info(f"Create user virtual network: {response.status_code}")
        if not response:
            return False
        return response.parsed

    async def get_marz_user(self, name_user_virtual_network: str) -> UserResponse:
        """
        Получает пользователя виртуальной сети из системы
        :param name_user_virtual_network: Название пользователя виртуальной сети.
        """
        response: Response = await get_user.asyncio_detailed(
            name_user_virtual_network, client=await self._client.get_client()
        )
        return response.parsed

    async def add_traffic_to_marz_user(
        self, name_user_virtual_network: str, value: int
    ) -> Response:
        """
        Расширяет лимит трафика пользователя виртуальной сети
        :param name_user_virtual_network:  Название пользователя виртуальной сети.
        :param value: Новое значение лимита
        """
        user_data = UserModify(data_limit=value)
        response: Response = await modify_user.asyncio_detailed(
            name_user_virtual_network,
            client=await self._client.get_client(),
            body=user_data,
        )
        return response.parsed

    async def get_user_virtual_network_links(
        self, name_user_virtual_network: str
    ) -> dict[str, str]:
        """
        Получает все ключи для подключения к виртуальной сети.
        :param name_user_virtual_network: Название пользователя виртуальной сети.
        :return: Строка содержащая ключи подключения к виртуальной сети.
        """
        response: UserResponse = await self.get_marz_user(name_user_virtual_network)
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
        return keys

    @staticmethod
    def expire_timestamp(expire: datetime):
        """Конвертация даты"""
        new_utc_timestamp = int(expire.timestamp())
        return new_utc_timestamp


marzban_client = MarzBanClient(marzban_settings.URL, logger=logger)
marzban_manager = MarzBanManager(logger, marzban_client)


async def main():
    data = await marzban_manager.get_user_virtual_network_links(
        name_user_virtual_network="user_3"
    )
    print(data)


if __name__ == "__main__":
    asyncio.run(main())
