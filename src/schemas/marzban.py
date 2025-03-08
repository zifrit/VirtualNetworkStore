from src.schemas.base import BaseSchema


class BaseMarzbanServiceSchema(BaseSchema):
    id: int
    name: str
    count_users: int


class ShowMarzbanServiceSchema(BaseMarzbanServiceSchema):
    pass
