from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from sqlalchemy import text
from . import crud, database, models
from app.api.genes import gene_router

@asynccontextmanager
async def lifespan(app: FastAPI):
    async with database.engine.begin() as conn:
        await conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm"))
        await conn.run_sync(models.Base.metadata.create_all)
    async with database.AsyncSessionLocal() as db:
        await crud.warmup_gene_cache(db, database.redis_client)
    
    yield

    await database.redis_client.close()

    
app = FastAPI(lifespan=lifespan)
app.include_router(gene_router, prefix="/api/v1/genes", tags=["Genes Management"])

@app.get("/")
def root():
    return {"message": "Welcome to DNA Library API"}
