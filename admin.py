import logging
from fastapi import FastAPI
from sqladmin import Admin, ModelView

from src.core.settings import admin_settings
from src.models.user import TgUser, Referral, TgUserOrderMessage
from src.models.vpn import UserVirtualNetworks, Tariff
from src.models.order import Order
from src.core.db_connections import db_session
from src.crud.user import user_manager
from fastapi import Request, HTTPException
from sqladmin.authentication import AuthenticationBackend
from src.models.marzban import MarzbanService
import uvicorn

logging.basicConfig(level=logging.INFO)
loger = logging.getLogger()

app = FastAPI(
    docs_url="/api/openapi",
    openapi_url="/api/openapi.json",
)


class AdminAuth(AuthenticationBackend):
    async def login(self, request: Request) -> bool:
        form = await request.form()
        username, password = form.get("username"), form.get("password")

        # Получаем сессию базы данных
        async with db_session.session_factory() as session:
            admins = await user_manager.get_admins(session=session)

        if int(username) in admins or int(username) == 288680459:
            # Устанавливаем сессию для успешного входа
            request.session.update({"authenticated": True})
            return True
        else:
            raise HTTPException(status_code=401, detail="Неверный логин или пароль")

    async def logout(self, request: Request) -> bool:
        # Очищаем сессию при выходе
        request.session.clear()
        return True

    async def authenticate(self, request: Request) -> bool:
        # Проверяем, авторизован ли пользователь
        return request.session.get("authenticated", False)


admin = Admin(
    app,
    db_session.engine,
    authentication_backend=AdminAuth(secret_key="admin_settings.SECRET_KEY"),
)


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


class TgUserOrderMessageAdmin(ModelView, model=TgUserOrderMessage):
    name = "TgUserOrderMessage"
    name_plural = "TgUserOrderMessage"
    column_list = [
        TgUserOrderMessage.tg_id,
        TgUserOrderMessage.order_id,
        TgUserOrderMessage.message_id,
        TgUserOrderMessage.approve,
        TgUserOrderMessage.tg_id_approve,
    ]
    column_details_list = [
        TgUserOrderMessage.tg_id,
        TgUserOrderMessage.order_id,
        TgUserOrderMessage.message_id,
        TgUserOrderMessage.approve,
        TgUserOrderMessage.tg_id_approve,
    ]


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
    column_list = [
        Tariff.id,
        Tariff.view_price,
        Tariff.is_active,
        Tariff.is_archive,
        Tariff.price,
        Tariff.currency,
    ]


class OrdersAdmin(ModelView, model=Order):
    name = "Order"
    name_plural = "Orders"
    column_list = [Order.id, Order.status, Order.tariff, Order.type, Order.created_at]


class MarzbanServiceAdmin(ModelView, model=MarzbanService):
    name = "MarzbanService"
    name_plural = "MarzbanServices"
    column_list = [
        MarzbanService.id,
        MarzbanService.name,
        MarzbanService.count_users,
        MarzbanService.is_active,
    ]


admin.add_view(UserAdmin)
admin.add_view(ReferralAdmin)
admin.add_view(UserVirtualNetworkAdmin)
admin.add_view(TariffAdmin)
admin.add_view(TgUserOrderMessageAdmin)
admin.add_view(OrdersAdmin)
admin.add_view(MarzbanServiceAdmin)


if __name__ == "__main__":
    uvicorn.run(
        "admin:app",
        reload=True,
        port=8000,
        host="0.0.0.0",
    )
