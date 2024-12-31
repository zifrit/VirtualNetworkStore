import logging
from fastapi import FastAPI
from sqladmin import Admin, ModelView

from src.core.db_connections import db_session
from src.models.user import TgUser
from src.models.vpn import UserVirtualNetworks, Country, Tariff
from src.models.order import Order
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


class VPNAdmin(ModelView, model=UserVirtualNetworks):
    name = "UserVirtualNetworks"
    name_plural = "UserVirtualNetworks"
    column_list = [
        UserVirtualNetworks.id,
        UserVirtualNetworks.virtual_network_key,
        UserVirtualNetworks.type_virtual_networks,
    ]


class PriceAdmin(ModelView, model=Country):
    name = "Country"
    name_plural = "Countries"
    column_list = [Country.id, Country.key_country, Country.view_country]


class UserVPNAdmin(ModelView, model=Tariff):
    name = "Tariff"
    name_plural = "Tariffs"
    column_list = [Tariff.id, Tariff.view_price, Tariff.price, Tariff.currency]


class OrdersAdmin(ModelView, model=Order):
    name = "Order"
    name_plural = "Orders"
    column_list = [Order.id, Order.status, Order.tariff]


admin.add_view(UserAdmin)
admin.add_view(VPNAdmin)
admin.add_view(PriceAdmin)
admin.add_view(UserVPNAdmin)
admin.add_view(OrdersAdmin)


if __name__ == "__main__":
    uvicorn.run(
        "admin:app",
        reload=True,
    )
