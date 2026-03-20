from fastapi import FastAPI, Depends, HTTPException
from sqlalchemy.orm import Session
#from . import schemas, database, models
from . import crud, schemas, database

app = FastAPI()

async def get_db():
    async with database.AsyncSessionlocal() as session:
        yield session

@app.post("/genes/", response_model=schemas.Gene)
async def create_gene(gene: schemas.GeneCreate, db: database.AsyncSession = Depends(get_db)):
    existing_gene = await crud.get_genes_by_label(db, label=gene.label)
    if existing_gene:
        raise HTTPException(status_code=400, detail="Gene with this label already exists")
    return await crud.create_gene(db=db, gene=gene)

@app.get("/genes/search", response_model=list[schemas.Gene])
async def search_genes(q: str, db: database.AsyncSession = Depends(get_db)):
    db_genes = await crud.get_genes_by_sequence(db, sequence=q)
    return db_genes

@app.get("/genes/{gene_id}", response_model=schemas.Gene)
async def read_gene(gene_id: int, db: database.AsyncSession = Depends(get_db)):
    db_gene = await crud.get_gene_with_stats(db, gene_id=gene_id)
    if db_gene is None:
        raise HTTPException(status_code=404, detail="Gene not found")
    return db_gene

@app.delete("/genes/{gene_id}", response_model=schemas.Gene)
async def delete_gene(gene_id: int, db: database.AsyncSession = Depends(get_db)):
    db_gene = await crud.delete_gene(db, gene_id=gene_id)
    if db_gene is None:
        raise HTTPException(status_code=404, detail="Gene not found")
    return {"message": "Done"}

@app.put("/genes/{gene_id}", response_model=schemas.Gene)
async def update_gene(gene_id: int, gene: schemas.GeneCreate, db: database.AsyncSession = Depends(get_db)):
    try:
        db_gene = await crud.update_gene(db, gene_id=gene_id, gene=gene)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    if db_gene is None:
        raise HTTPException(status_code=404, detail="Gene not found")
    return db_gene