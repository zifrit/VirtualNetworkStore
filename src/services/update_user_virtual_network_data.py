from datetime import datetime
from src.crud.virtual_network import user_virtual_networks_manager
from src.models.vpn import UserVirtualNetworks
from src.core.db_connections import db_session


async def update_user_virtual_network_data(data: dict) -> None:
    async with db_session.session_factory() as session:
        marz_virtual_network_keys = data.keys()
        user_virtual_networks = (
            await user_virtual_networks_manager.get_user_virtual_network_by_marzban(
                session=session,
                marz_virtual_network_keys=list(marz_virtual_network_keys),
            )
        )
        for user_virtual_network in user_virtual_networks:  # type: UserVirtualNetworks
            user_virtual_network.traffic_limit = await convert_byte_to_gigabytes(
                data[user_virtual_network.virtual_network_key]["data_limit"]
            )
            user_virtual_network.status = data[
                user_virtual_network.virtual_network_key
            ]["status"]

            user_virtual_network.used_traffic = await convert_byte_to_gigabytes(
                data[user_virtual_network.virtual_network_key]["used_traffic"]
            )

            user_virtual_network.expire = await convert_timestamp_to_datetime(
                data[user_virtual_network.virtual_network_key]["expire"]
            )
        await session.commit()


async def convert_timestamp_to_datetime(timestamp: int):
    return datetime.fromtimestamp(timestamp)


async def convert_byte_to_gigabytes(bytes_: int):
    return round(bytes_ / 1024**3, 2)
