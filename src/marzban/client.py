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
from sqlalchemy.util import await_only

from core.db_connections import db_session
from crud.marzban import marzban_service_manager
from crud.virtual_network import tariff_manager
from services.update_user_virtual_network_data import update_user_virtual_network_data
from src.core.settings import marzban_settings, MarzbanSettings


logger = logging.getLogger(__name__)
admin_logger = logging.getLogger("admin_log")


class MarzBanClient:
    def __init__(self, marz_settings: MarzbanSettings, logger: Logger):
        self._clients: dict[str, dict[str, AuthenticatedClient | datetime]] = dict(
            dict()
        )
        self._marz_settings: MarzbanSettings = marz_settings
        self._logger = logger
        self._token: str = ""

    async def get_client(self, prefix: str = "PANDA") -> AuthenticatedClient:
        """
        Получение клиента для работы с системой
        :return:
        """
        if (
            self._clients.get(prefix)
            and self._clients[prefix]["exp_at"] > datetime.now()
        ):
            self._logger.info(f"Return exist client")
            return self._clients.get(prefix)["client"]
        cred = self._marz_settings.get_cred(prefix=prefix)
        self._logger.info(f"Get new token")
        token = await self.get_token(
            username=cred["username"],
            password=cred["password"],
            base_url=cred["url"],
        )
        self._logger.info(f"Create client")
        new_client = AuthenticatedClient(
            base_url=cred["url"], token=token, verify_ssl=True
        )
        exp_at = datetime.now() + timedelta(minutes=1440)
        self._clients[prefix] = {
            "client": new_client,
            "exp_at": exp_at,
        }
        return new_client

    async def get_token(self, username: str, password: str, base_url: str) -> str:
        """
        Осуществляется вход в систему и получается токен для дальнейшей работы с клиентом
        :return:
        """
        try:
            login_data = BodyAdminTokenApiAdminTokenPost(
                username=username,
                password=password,
            )
            async with Client(base_url=base_url) as client:
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
        marzban_service_name: str,
        data_limit: int = 200 * 1024**3,
    ) -> Response | bool:
        """
        Создание пользователя виртуальной сети в системе.
        :param marzban_service_name: Название марзбан сервера
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
                client=await self._client.get_client(prefix=marzban_service_name),
                body=user_data,
            )
            self._logger.info(
                "Created %s virtual network in %s. Status code %s",
                name_user_virtual_network,
                marzban_service_name,
                response.status_code,
            )
            return response.parsed
        except httpx.RequestError as e:
            self._logger.error(
                "When create_virtual_network from %s happened error: %s",
                marzban_service_name,
                e,
            )
            return False

    async def get_marz_user_virtual_network(
        self,
        name_user_virtual_network: str,
        marzban_service_name: str,
    ) -> UserResponse | bool:
        """
        Получает пользователя виртуальной сети из системы
        :param marzban_service_name: Название марзбан сервера
        :param name_user_virtual_network: Название пользователя виртуальной сети.
        """
        try:
            response: Response = await get_user.asyncio_detailed(
                name_user_virtual_network,
                client=await self._client.get_client(prefix=marzban_service_name),
            )
            self._logger.info(
                "Get '%s' from %s virtual network data. Status code %s",
                name_user_virtual_network,
                marzban_service_name,
                response.status_code,
            )
            return response.parsed
        except httpx.RequestError as e:
            self._logger.error(
                "When get_marz_user_virtual_network from %s happened error: %s",
                marzban_service_name,
                e,
            )
            return False

    async def update_traffic_to_marz_user(
        self, name_user_virtual_network: str, value: int, marzban_service_name: str
    ) -> Response | bool:
        """
        Расширяет лимит трафика пользователя виртуальной сети
        :param marzban_service_name: Название марзбан сервера
        :param name_user_virtual_network:  Название пользователя виртуальной сети.
        :param value: Новое значение лимита
        """
        user_data = UserModify(
            data_limit=value,
        )
        try:
            response: Response = await modify_user.asyncio_detailed(
                name_user_virtual_network,
                client=await self._client.get_client(prefix=marzban_service_name),
                body=user_data,
            )
            self._logger.info(
                "Virtual network '%s' from %s set %s data limit",
                name_user_virtual_network,
                marzban_service_name,
                value,
            )
            return response.parsed
        except httpx.RequestError as e:
            self._logger.error(
                "When update_traffic_to_marz_user from %s happened error: %s",
                marzban_service_name,
                e,
            )
            return False

    async def update_expire_to_marz_user(
        self,
        name_user_virtual_network: str,
        extend_date_by: int,
        marzban_service_name: str,
    ) -> Response | bool:
        """
        Расширяет срок жизни пользователя виртуальной сети
        :param marzban_service_name: Название марзбан сервера
        :param name_user_virtual_network:  Название пользователя виртуальной сети.
        :param extend_date_by: На сколько расширится срок жизни виртуальной сети
        """
        user_virtual_network = await self.get_marz_user_virtual_network(
            name_user_virtual_network=name_user_virtual_network,
            marzban_service_name=marzban_service_name,
        )
        if not user_virtual_network:
            return False

        old_expire = datetime.fromtimestamp(user_virtual_network.expire)

        new_expire = MarzBanManager.expire_timestamp(
            old_expire - timedelta(days=extend_date_by)
        )
        user_data = UserModify(expire=new_expire)
        try:
            response: Response = await modify_user.asyncio_detailed(
                name_user_virtual_network,
                client=await self._client.get_client(prefix=marzban_service_name),
                body=user_data,
            )
            self._logger.info(
                "Virtual network '%s' from %s extended expire to %s ",
                name_user_virtual_network,
                marzban_service_name,
                old_expire + timedelta(days=extend_date_by),
            )
            return response.parsed
        except httpx.ReadError as e:
            self._logger.error(
                "When update_expire_to_marz_user from %s happened error: %s",
                marzban_service_name,
                e,
            )
            return False

    async def get_user_virtual_network_links(
        self, name_user_virtual_network: str, marzban_service_name: str
    ) -> dict[str, str] | bool:
        """
        Получает все ключи для подключения к виртуальной сети.
        :param marzban_service_name: Название марзбан сервера
        :param name_user_virtual_network: Название пользователя виртуальной сети.
        :return: Строка содержащая ключи подключения к виртуальной сети.
        """
        try:
            response: UserResponse = await self.get_marz_user_virtual_network(
                name_user_virtual_network, marzban_service_name=marzban_service_name
            )
        except httpx.ReadError as e:
            self._logger.error(
                "When get_user_virtual_network_links from %s happened error: %s",
                marzban_service_name,
                e,
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
            "Get '%s' from %s Virtual network links: %s",
            name_user_virtual_network,
            marzban_service_name,
            keys,
        )
        return keys

    async def delete_user_virtual_network(
        self, name_user_virtual_network: str, marzban_service_name: str
    ) -> None:
        """
        Удаляет виртуальную сеть пользователя, уменьшая его срок жизни на 10 дней после чего удаляю всех у кого больше 10 как истек строк жизни.
        :param marzban_service_name: Название марзбан сервера
        :param name_user_virtual_network: Название пользователя виртуальной сети.
        :return: None
        """
        ten_days = MarzBanManager.expire_timestamp(
            datetime.now(timezone.utc) - timedelta(days=10)
        )
        user_data = UserModify(expire=ten_days)
        await modify_user.asyncio_detailed(
            name_user_virtual_network,
            client=await self._client.get_client(prefix=marzban_service_name),
            body=user_data,
        )

        delete_utc_time = datetime.now(timezone.utc) - timedelta(days=9, hours=23)
        await delete_expired_users.asyncio_detailed(
            expired_before=delete_utc_time,
            client=await self._client.get_client(prefix=marzban_service_name),
        )
        self._logger.info(
            "Virtual network '%s' from %s deleted",
            name_user_virtual_network,
            marzban_service_name,
        )

    async def reset_user_virtual_network_data_usage(
        self, name_user_virtual_network: str, marzban_service_name: str
    ) -> None:
        """
        Сбрасывает количество потраченного трафика у виртуальной сети пользователя.
        :param marzban_service_name: Название марзбан сервера
        :param name_user_virtual_network: Название пользователя виртуальной сети.
        :return: None
        """

        await reset_user_data_usage.asyncio_detailed(
            client=await self._client.get_client(prefix=marzban_service_name),
            username=name_user_virtual_network,
        )
        self._logger.info(
            "Virtual network '%s' reset traffic data", name_user_virtual_network
        )

    async def reset_virtual_network_data(
        self, name_user_virtual_network: str, tariff_id: int, marzban_service_name: str
    ) -> None:
        """

        :param marzban_service_name: Название марзбан сервера
        :param name_user_virtual_network: Название пользователя виртуальной сети.
        :param tariff_id: Идентификатор тарифа
        :return:
        """
        await self.reset_user_virtual_network_data_usage(
            name_user_virtual_network=name_user_virtual_network,
            marzban_service_name=marzban_service_name,
        )
        session = await self._db_client
        tariff = await tariff_manager.get_active_tariff_by_id(
            tariff_id=tariff_id, session=session
        )

        await self.update_traffic_to_marz_user(
            name_user_virtual_network=name_user_virtual_network,
            marzban_service_name=marzban_service_name,
            value=tariff.traffic_limit,
        )

    async def ping(self) -> None:
        """
        Делает запрос на получения всех пользователей, сейчас выступает в роли проверки доступа к серверу
        :return:
        """
        for marzban_service_name in await marzban_service_manager.get_services(
            session=await self._db_client
        ):
            response: Response = await get_users.asyncio_detailed(
                client=await self._client.get_client(prefix=marzban_service_name),
            )
            user_virtual_network_data = await self.search_user_virtual_network_data(
                response.parsed.to_dict()["users"]
            )
            await update_user_virtual_network_data(data=user_virtual_network_data)
            if response.status_code == 200:
                self._logger.info(
                    "Sever %s is work, code: %s",
                    marzban_service_name,
                    response.status_code,
                )
            else:
                self._logger.error(
                    "Server %s returned unexpected status code: %s",
                    marzban_service_name,
                    response.status_code,
                )

    async def get_users_(self):
        response: Response = await get_users.asyncio_detailed(
            client=await self._client.get_client(),
        )
        user_virtual_network_data = await self.search_user_virtual_network_data(
            response.parsed.to_dict()["users"]
        )

    @staticmethod
    async def search_user_virtual_network_data(
        datas: dict,
    ) -> dict[str, dict[str, str]]:
        result = {}
        for data in datas:
            result[data["username"]] = {
                "status": data["status"],
                "used_traffic": data["used_traffic"],
                "data_limit": data["data_limit"],
                "expire": data["expire"],
            }
        return result

    @staticmethod
    def expire_timestamp(expire: datetime):
        """Конвертация даты"""
        new_utc_timestamp = int(expire.timestamp())
        return new_utc_timestamp


marzban_client = MarzBanClient(marzban_settings, logger=logger)
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

    # data = await marzban_manager.add_traffic_to_marz_user(
    #     name_user_virtual_network="zifrit_Bt0NdnFG", value=200
    # )
    # timedelta(days=1)
    r = await marzban_manager.ping()
    print(r.to_dict())
    user = r.to_dict()["user"]
    for item, key in r.to_dict().items():
        print(item)
        print(key)
    # print(data.created_at)
    # print(datetime.fromtimestamp(data.on_hold_expire_duration))
    # print(datetime.fromtimestamp(data.expire) - timedelta(days=30))
    # a = datetime.fromtimestamp(data.expire)
    # b = datetime.now()
    # c = a - b
    # print(c < timedelta(days=1))


if __name__ == "__main__":
    asyncio.run(main())
