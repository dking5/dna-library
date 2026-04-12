from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from sqlalchemy import text
from . import crud, database, models
from app.api.genes import gene_router
from .core.redis import redis_manager
from prometheus_fastapi_instrumentator import Instrumentator
from app.core.limiter import limiter
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup: Initialize Redis connection
    await redis_manager.connect()

    # Set up PostgresSQL extensions and tables, then warm up Redis cache
    async with database.engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS vector"))
        await conn.run_sync(models.Base.metadata.create_all)
    async with database.AsyncSessionLocal() as db:
        await crud.warmup_gene_cache(db, redis_manager.client)
    
    yield
    # Shutdown: Clean up resources
    await redis_manager.disconnect()

app = FastAPI(lifespan=lifespan)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

@app.get("/health/redis")
async def check_redis():
    is_alive = await redis_manager.client.ping()
    return {"redis_active": is_alive}


app.include_router(gene_router, prefix="/api/v1/genes", tags=["Genes Management"])

@app.get("/")
def root():
    return {"message": "Welcome to DNA Library API"}

Instrumentator().instrument(app).expose(app)