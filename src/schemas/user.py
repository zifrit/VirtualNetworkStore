from src.schemas.base import BaseSchema


class UserSchema(BaseSchema):
    username: str
    tg_id: int


class CreateUserSchema(UserSchema):
    pass


class ReferralSchema(BaseSchema):
    referrer_tg_id: int
    referred_tg_id: int


class CreateReferralSchema(ReferralSchema):
    pass
