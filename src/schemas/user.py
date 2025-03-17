from src.schemas.base import BaseSchema


class TgUserSchema(BaseSchema):
    username: str
    tg_id: int


class ShowTgUserSchema(TgUserSchema):
    pass


class CreateTgUserSchema(TgUserSchema):
    pass


class ReferralSchema(BaseSchema):
    referrer_tg_id: int
    referred_tg_id: int


class CreateReferralSchema(ReferralSchema):
    pass


class TgUserOrderMessageSchema(BaseSchema):
    order_id: int
    tg_id: int
    message_id: int


class CreateTgUserOrderMessageSchema(TgUserOrderMessageSchema):
    pass
