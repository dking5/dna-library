from contextlib import asynccontextmanager
import json
from linecache import cache
from fastapi import APIRouter, FastAPI, Depends, HTTPException, UploadFile, File, BackgroundTasks
from redis import Redis
from sqlalchemy import select,text
from . import crud, schemas, database, models
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
app.include_router(gene_router, prefix="/api/v1", tags=["Genes Management"])

@app.post("/genes/", response_model=schemas.Gene)
async def create_gene(gene: schemas.GeneCreate, db: database.AsyncSession = Depends(database.get_db)):
    existing_gene = await crud.get_genes_by_label(db, label=gene.label)
    if existing_gene:
        raise HTTPException(status_code=400, detail="Gene with this label already exists")
    return await crud.create_gene(db=db, gene=gene)

@app.post("/genes/upload-fasta/", status_code=202)
async def upload_fasta(background_tasks: BackgroundTasks, file: UploadFile = File(...), db: database.AsyncSession = Depends(database.get_db), cache = Depends(database.get_redis)):
    if not file.filename.endswith((".fasta", ".fa")):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a FASTA file.")
    
    content = await file.read()
    fasta_str = content.decode("utf-8")
    background_tasks.add_task(process_fasta_in_background, db=db, fasta_str=fasta_str, cache=cache)
    return {"message": "File uploaded successfully. Processing in background..."}

@app.get("/genes/search", response_model=list[schemas.Gene])
async def search_genes(q: str, db: database.AsyncSession = Depends(database.get_db), cache = Depends(database.get_redis)):
    cache_key = f"search:{q.upper()}"
    cached_data = await cache.get(cache_key)
    if cached_data:
        print("Redis Cache Hit!")
        return json.loads(cached_data)
    
    print("Postgres Querying...")
    db_genes = await crud.get_genes_by_sequence(db, sequence=q)
    results_as_dict = [
        {"id": g.id, "label": g.label, "gc_content": g.gc_content, "sequence": g.sequence, "description": g.description, "created_at": g.created_at.isoformat() if g.created_at else None} 
        for g in db_genes
    ]
    await cache.set(cache_key, json.dumps(results_as_dict), ex=3600)
    return db_genes

@app.get("/genes/{gene_id}", response_model=schemas.Gene)
async def read_gene(gene_id: int, db: database.AsyncSession = Depends(database.get_db)):
    db_gene = await crud.get_gene_with_stats(db, gene_id=gene_id)
    if db_gene is None:
        raise HTTPException(status_code=404, detail="Gene not found")
    return db_gene

@app.delete("/genes/{gene_id}", response_model=schemas.Gene)
async def delete_gene(gene_id: int, db: database.AsyncSession = Depends(database.get_db)):
    db_gene = await crud.delete_gene(db, gene_id=gene_id)
    if db_gene is None:
        raise HTTPException(status_code=404, detail="Gene not found")
    return {"message": "Done"}

@app.put("/genes/{gene_id}", response_model=schemas.Gene)
async def update_gene(gene_id: int, gene: schemas.GeneCreate, db: database.AsyncSession = Depends(database.get_db)):
    try:
        db_gene = await crud.update_gene(db, gene_id=gene_id, gene=gene)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if db_gene is None:
        raise HTTPException(status_code=404, detail="Gene not found")
    return db_gene

async def process_fasta_in_background(db: database.AsyncSession, fasta_str: str, cache):
    print("[Background] Starting to parse FASTA...")
    num_genes = await crud.bulk_create_genes_from_fasta(db, fasta_content=fasta_str)
    if num_genes > 0:
        keys = []
        async for key in cache.scan_iter("search:*"):
            keys.append(key)
        if keys:
            async with cache.pipeline(transaction=False) as pipe:
                for key in keys:
                    await pipe.unlink(key)
                await pipe.execute()
        print("[Background] Cleared Redis Cache after FASTA upload.")
    else :
        print("[Background] No genes were created from the FASTA file.")
