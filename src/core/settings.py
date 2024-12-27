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


db_settings = Database()
bot_settings = Settings()

bot = Bot(
    token=bot_settings.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dp = Dispatcher(storage=MemoryStorage())
