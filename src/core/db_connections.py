from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from src.core.settings import db_settings


class DatabaseHelper:
    def __init__(self, db_url):
        self.engine = create_async_engine(
            url=db_url,
            echo=False,
        )
        self.session_factory = async_sessionmaker(
            bind=self.engine,
            autoflush=False,
            autocommit=False,
            expire_on_commit=False,
        )

    async def get_session(self) -> AsyncSession:
        async with self.session_factory() as session:
            yield session
            await session.close()


db_session = DatabaseHelper(db_settings.database_url_asyncpg)
