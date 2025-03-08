import logging
from fastapi import FastAPI
from sqladmin import Admin, ModelView

from src.core.db_connections import db_session
from src.models.user import TgUser, Referral
from src.models.vpn import UserVirtualNetworks, Tariff
from src.models.order import Order
from src.models.marzban import MarzbanService
import uvicorn

logging.basicConfig(level=logging.INFO)
loger = logging.getLogger()

app = FastAPI(
    docs_url="/api/openapi",
    openapi_url="/api/openapi.json",
)
admin = Admin(app, db_session.engine)


class UserAdmin(ModelView, model=TgUser):
    name = "User"
    name_plural = "Users"
    column_list = [TgUser.tg_id, TgUser.username]
    column_details_list = [TgUser.tg_id, TgUser.username]


class ReferralAdmin(ModelView, model=Referral):
    name = "Referral"
    name_plural = "Referrals"
    # column_list = [TgUser.tg_id, TgUser.username]
    # column_details_list = [TgUser.tg_id, TgUser.username]


class UserVirtualNetworkAdmin(ModelView, model=UserVirtualNetworks):
    name = "UserVirtualNetworks"
    name_plural = "UserVirtualNetworks"
    column_list = [
        UserVirtualNetworks.id,
        UserVirtualNetworks.virtual_network_key,
        UserVirtualNetworks.type_virtual_networks,
        UserVirtualNetworks.marzban_service,
        UserVirtualNetworks.deleted_at,
        UserVirtualNetworks.used_traffic,
        UserVirtualNetworks.traffic_limit,
    ]


class TariffAdmin(ModelView, model=Tariff):
    name = "Tariff"
    name_plural = "Tariffs"
    column_list = [Tariff.id, Tariff.view_price, Tariff.price, Tariff.currency]


class OrdersAdmin(ModelView, model=Order):
    name = "Order"
    name_plural = "Orders"
    column_list = [Order.id, Order.status, Order.tariff, Order.type]


class MarzbanServiceAdmin(ModelView, model=MarzbanService):
    name = "MarzbanService"
    name_plural = "MarzbanServices"
    column_list = [MarzbanService.id, MarzbanService.name, MarzbanService.count_users]


admin.add_view(UserAdmin)
admin.add_view(ReferralAdmin)
admin.add_view(UserVirtualNetworkAdmin)
admin.add_view(TariffAdmin)
admin.add_view(OrdersAdmin)
admin.add_view(MarzbanServiceAdmin)


if __name__ == "__main__":
    uvicorn.run(
        "admin:app",
        reload=True,
    )
