from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
from dotenv import load_dotenv
from pydantic_settings import BaseSettings

load_dotenv()


class Settings(BaseSettings):
    BOT_TOKEN: str
    ADMINS: tuple = (288680459,)


class Database(BaseSettings):
    database_url_asyncpg: str = "sqlite+aiosqlite:///db.sqlite3"


class RedisSettings(BaseSettings):
    host: str = "localhost"
    port: int = 6379


class MarzbanSettings(BaseSettings):
    URL: str = "http://127.0.0.1:8111"
    USERNAME: str = "admin"
    PASSWORD: str = "Hw3lhDgLThXO"


db_settings = Database()
bot_settings = Settings()
redis_settings = RedisSettings()
marzban_settings = MarzbanSettings()

bot = Bot(
    token=bot_settings.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dp = Dispatcher(storage=MemoryStorage())
