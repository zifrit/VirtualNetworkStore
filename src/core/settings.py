import os

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage
from aiogram.enums import ParseMode
from dotenv import load_dotenv
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict

load_dotenv()


class Settings(BaseSettings):
    BOT_TOKEN: str


class AdminSettings(BaseSettings):
    SECRET_KEY: str


class Database(BaseSettings):
    DB_HOST: str = "localhost"
    DB_PORT: int = 5432
    DB_USER: str = "postgres"
    DB_PASS: str = "postgres"
    DB_NAME: str = "vpn_market"

    @property
    def database_url_asyncpg(self):
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASS}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"


class RedisSettings(BaseSettings):
    host: str = "localhost"
    port: int = 6379


class MarzbanSettings(BaseSettings):
    M_URL: str = Field(default="None")
    M_USERNAME: str = Field(default="None")
    M_PASSWORD: str = Field(default="None")

    def _reload_from_env(self, prefix: str) -> None:
        """
        Перезагружает значение из окружения для текущего ключа
        """
        env_value_1 = os.getenv(f"{prefix}_M_USERNAME")
        env_value_2 = os.getenv(f"{prefix}_M_PASSWORD")
        env_value_3 = os.getenv(f"{prefix}_M_URL")
        if env_value_1 and env_value_2 and env_value_3:
            self.M_USERNAME = env_value_1
            self.M_PASSWORD = env_value_2
            self.M_URL = env_value_3

    def get_cred(self, prefix: str) -> dict[str, str]:
        self._reload_from_env(prefix)
        return {
            "url": self.M_URL,
            "username": self.M_USERNAME,
            "password": self.M_PASSWORD,
        }


db_settings = Database()
admin_settings = AdminSettings()
bot_settings = Settings()
redis_settings = RedisSettings()
marzban_settings = MarzbanSettings()

bot = Bot(
    token=bot_settings.BOT_TOKEN,
    default=DefaultBotProperties(parse_mode=ParseMode.HTML),
)
dp = Dispatcher(storage=MemoryStorage())
