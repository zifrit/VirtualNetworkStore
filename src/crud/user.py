from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.user import TgUser, Referral
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
                referred_user_id=obj_schema.referred_user,
                referrer_id=obj_schema.referrer_user,
            )
            session.add(referral)
            await session.commit()
            return True
        return False


referral_manager = ReferralManager(Referral)
