
from sqlalchemy.orm import sessionmaker, declarative_base
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession

from configs.config import MYSQL_URI

Base = declarative_base()
engine = create_async_engine(MYSQL_URI, encoding="utf-8", echo=True, max_overflow=5)

async_session = sessionmaker(
    engine, expire_on_commit=False, class_=AsyncSession
)
