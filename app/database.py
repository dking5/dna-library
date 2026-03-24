import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base
import redis.asyncio as redis

load_dotenv()

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./default.db")
engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=True)
AsyncSessionlocal = sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)
Base = declarative_base()

async def get_db():
    async with AsyncSessionlocal() as session:
        yield session

redis_client = redis.from_url("redis://localhost:6379",decode_responses=True)

async def get_redis():
    yield redis_client