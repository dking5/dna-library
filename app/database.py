#from sqlalchemy import create_engine
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker, declarative_base


SQLALCHEMY_DATABASE_URL = "sqlite+aiosqlite:///./dna_app.db"

engine = create_async_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})

#SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
AsyncSessionlocal = sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
Base = declarative_base()