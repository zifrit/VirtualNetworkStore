from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from src.models.user import TgUser, Referral, TgUserOrderMessage
from src.models.vpn import UserVirtualNetworks
from src.crud.base import BaseManager
from src.schemas.user import CreateReferralSchema


class UserManager(BaseManager[TgUser]):

    async def get_by_tg_id(
        self, session: AsyncSession, id_: int, *args, **kwargs
    ) -> TgUser:
        result = await session.scalar(
            select(self._model).where(
                self._model.tg_id == id_,
                self._model.deleted_at.is_(None),
            )
        )
        return result

    async def get_user_virtual_network(
        self,
        session: AsyncSession,
        id_: int,
        *args,
        **kwargs,
    ) -> TgUser:
        result = await session.scalar(
            select(self._model)
            .options(
                selectinload(
                    TgUser.user_virtual_networks.and_(
                        UserVirtualNetworks.deleted_at.is_(None)
                    )
                ).load_only(
                    UserVirtualNetworks.id, UserVirtualNetworks.virtual_network_key
                )
            )
            .where(
                self._model.tg_id == id_,
                self._model.deleted_at.is_(None),
            )
        )
        return result

    async def get_admins(self, session: AsyncSession) -> list[int]:
        result = await session.scalars(
            select(self._model.tg_id).where(
                self._model.is_admin.is_(True),
                self._model.deleted_at.is_(None),
                self._model.is_active.is_(True),
            )
        )
        return list(result)


user_manager = UserManager(TgUser)


class ReferralManager(BaseManager[Referral]):

    async def create(
        self,
        session: AsyncSession,
        obj_schema: CreateReferralSchema,
        *args,
        **kwargs,
    ) -> bool:
        is_referral = await session.scalar(
            select(Referral).where(
                Referral.referred_user_id == obj_schema.referrer_tg_id
            )
        )
        if not is_referral:
            referral = Referral(
                referred_user_id=obj_schema.referred_tg_id,
                referrer_id=obj_schema.referrer_tg_id,
            )
            session.add(referral)
            await session.commit()
            return True
        return False


referral_manager = ReferralManager(Referral)


class TgUserOrderMessageManager(BaseManager[TgUserOrderMessage]):
    async def get_by_order_id(
        self, session: AsyncSession, order_id: int
    ) -> list[TgUserOrderMessage]:
        result = await session.scalars(
            select(self._model).where(self._model.order_id == order_id)
        )
        return list(result)


tg_user_order_message_manager = TgUserOrderMessageManager(TgUserOrderMessage)
