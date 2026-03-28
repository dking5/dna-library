from fastapi import APIRouter, Depends, HTTPException
from app import crud
from app.database import AsyncSession, get_db, get_redis

gene_router = APIRouter()

@gene_router.post("/genes/merge/")
async def merge_genes(id_a: int, id_b: int, label: str, db: AsyncSession = Depends(get_db), redis = Depends(get_redis)):
    try:
        new_gene = await crud.merge_genes_atomic(db, redis, id_a=id_a, id_b=id_b, new_label=label)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        import traceback
        print(traceback.format_exc())
        raise HTTPException(status_code=500, detail="Internal Server Error during merge.")
    if new_gene is None:
        raise HTTPException(status_code=404, detail="One or both genes not found for merging.")
    return new_gene