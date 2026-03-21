import os
from dotenv import load_dotenv
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base

load_dotenv()

SQLALCHEMY_DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./default.db")

engine = create_async_engine(SQLALCHEMY_DATABASE_URL, echo=True)

#SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
AsyncSessionlocal = sessionmaker(bind=engine, expire_on_commit=False, class_=AsyncSession)
Base = declarative_base()