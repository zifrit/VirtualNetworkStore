from datetime import datetime

from src.models.vpn import StatusVirtualNetwork, TypeVirtualNetwork
from src.schemas.base import BaseSchema

class UserVirtualNetworksSchema(BaseSchema):
    virtual_network_key: str
    status: StatusVirtualNetwork
    type_virtual_networks: TypeVirtualNetwork
    virtual_networks: str
    expire: datetime
    traffic_limit: int = 200
    tg_used_traffic: int = 0
    tg_user_id: int

class CreateUserVirtualNetworkSchema(UserVirtualNetworksSchema):
    pass