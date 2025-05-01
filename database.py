from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.ext.declarative import declarative_base

SQL_DB_URL = 'sqlite+aiosqlite:///database.db'

engine = create_async_engine(SQL_DB_URL, connect_args={'check_same_thread': False})

session_local = async_sessionmaker(engine, expire_on_commit=False)

Base = declarative_base()


async def get_sessions():
    async with session_local() as session:
        yield session
