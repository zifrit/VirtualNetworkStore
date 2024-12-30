import logging
from fastapi import FastAPI
from sqladmin import Admin, ModelView

from src.core.db_connections import db_session
from src.models.user import TgUser
from src.models.vpn import UserVPNs, Country, Price
from src.models.order import Order, OrderReceipt
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


class VPNAdmin(ModelView, model=UserVPNs):
    name = "UserVPN"
    name_plural = "UserVPNs"
    column_list = [UserVPNs.id, UserVPNs.vpn_key, UserVPNs.type_VPN]


class PriceAdmin(ModelView, model=Country):
    name = "Country"
    name_plural = "Countries"
    column_list = [Country.id, Country.key_country, Country.view_country]


class UserVPNAdmin(ModelView, model=Price):
    name = "Price"
    name_plural = "Price"
    column_list = [Price.id, Price.view_price, Price.price, Price.currency]


class OrdersAdmin(ModelView, model=Order):
    name = "Order"
    name_plural = "Orders"
    column_list = [Order.id, Order.status, Order.price]


class PaymentsAdmin(ModelView, model=OrderReceipt):
    name = "Payment"
    name_plural = "Payments"
    column_list = [OrderReceipt.id, OrderReceipt.status, OrderReceipt.amount]


admin.add_view(UserAdmin)
admin.add_view(VPNAdmin)
admin.add_view(PriceAdmin)
admin.add_view(UserVPNAdmin)
admin.add_view(OrdersAdmin)
admin.add_view(PaymentsAdmin)


if __name__ == "__main__":
    uvicorn.run(
        "admin:app",
        reload=True,
    )
