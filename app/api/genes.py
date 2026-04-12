import json
from fastapi import APIRouter, Depends, HTTPException, Request, UploadFile, File, BackgroundTasks
from app import crud, schemas
from ..core.limiter import limiter, get_remote_address
from app.database import AsyncSession, get_db, get_redis
from app.services.ai_service import AIService
from app.api.deps import get_ai_service

gene_router = APIRouter(tags=["Genes Management"])

@gene_router.post("/", response_model=schemas.Gene)
async def create_gene(gene: schemas.GeneCreate, db: AsyncSession = Depends(get_db)):
    existing_gene = await crud.get_genes_by_label(db, label=gene.label)
    if existing_gene:
        raise HTTPException(status_code=400, detail="Gene with this label already exists")
    return await crud.create_gene(db=db, gene=gene)

@gene_router.post("/batches", status_code=202)
async def upload_fasta(background_tasks: BackgroundTasks, file: UploadFile = File(...), db: AsyncSession = Depends(get_db), cache = Depends(get_redis)):
    if not file.filename.endswith((".fasta", ".fa")):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a FASTA file.")
    
    content = await file.read()
    fasta_str = content.decode("utf-8")
    background_tasks.add_task(process_fasta_in_background, db=db, fasta_str=fasta_str, cache=cache)
    return {"message": "File uploaded successfully. Processing in background..."}

@gene_router.get("/searches", response_model=list[schemas.Gene])
async def search_genes(q: str, db: AsyncSession = Depends(get_db), cache = Depends(get_redis)):
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

@gene_router.get("/similarity-searches", response_model=list[schemas.Gene])
async def similarity_search_genes(sequence: str, db: AsyncSession = Depends(get_db)):
    return await crud.search_similar_genes(db, sequence)

@gene_router.get("/{gene_id}", response_model=schemas.Gene)
async def read_gene(gene_id: int, db: AsyncSession = Depends(get_db)):
    db_gene = await crud.get_gene_with_stats(db, gene_id=gene_id)
    if db_gene is None:
        raise HTTPException(status_code=404, detail="Gene not found")
    return db_gene

@gene_router.delete("/{gene_id}")
async def delete_gene(gene_id: int, db: AsyncSession = Depends(get_db)):
    db_gene = await crud.delete_gene(db, gene_id=gene_id)
    if db_gene is None:
        raise HTTPException(status_code=404, detail="Gene not found")
    return {"message": "Done"}

@gene_router.put("/{gene_id}", response_model=schemas.Gene)
async def update_gene(gene_id: int, gene: schemas.GeneCreate, db: AsyncSession = Depends(get_db)):
    try:
        db_gene = await crud.update_gene(db, gene_id=gene_id, gene=gene)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if db_gene is None:
        raise HTTPException(status_code=404, detail="Gene not found")
    return db_gene

async def process_fasta_in_background(db: AsyncSession, fasta_str: str, cache):
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

@gene_router.post("/merges/")
async def merge_genes(id_a: int, id_b: int, label: str, db: AsyncSession = Depends(get_db), redis = Depends(get_redis)):
    try:
        new_gene = await crud.merge_genes_atomic(db, redis, id_a=id_a, id_b=id_b, new_label=label)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Internal Server Error during merge.")
    if new_gene is None:
        raise HTTPException(status_code=404, detail="One or both genes not found for merging.")
    return new_gene

@gene_router.post("/{gene_id}/analyses", status_code=200)
@limiter.limit("1/minute", key_func=get_remote_address)
async def analyze_gene_with_ai(
    request: Request,
    gene_id: int, 
    db: AsyncSession = Depends(get_db),
    ai_service: AIService = Depends(get_ai_service)
):
    """
    Performs RAG-based analysis: 
    1. Fetches the target gene by ID.
    2. Searches for similar genes using pgvector.
    3. Generates a biological report via Gemini 2.0.
    """
    
    # 1. Fetch the target gene from PostgreSQL
    target_gene = await crud.get_gene_with_stats(db, gene_id)
    if not target_gene:
        raise HTTPException(status_code=404, detail="Gene not found")

    # 2. Retrieve context (Top 5 similar genes using your Week 2 vector search)
    # Assuming target_gene has an 'embedding' field
    similar_genes = await crud.search_similar_genes( 
        target_sequence=target_gene.sequence, 
        limit=5, 
        db=db
    )

    # 3. Generate the AI Report
    # This calls the async generate_dna_report we just built
    report_text = await ai_service.summarize_gene_function(
        target_gene=target_gene, 
        similar_genes=similar_genes
    )

    return {
        "gene_id": gene_id,
        "label": target_gene.label,
        "analysis_report": report_text,
        "references_used": [g.label for g in similar_genes]
    }