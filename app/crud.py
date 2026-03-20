from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from . import models, schemas

async def get_gene(db: AsyncSession, gene_id: int):
    result = await db.execute(select(models.Gene).where(models.Gene.id == gene_id))
    return result.scalars().first()

async def create_gene(db: AsyncSession, gene: schemas.GeneCreate):
    db_gene = models.Gene(**gene.model_dump())
    db.add(db_gene)
    await db.commit()
    await db.refresh(db_gene)
    return db_gene

def calculate_dna_stats(sequence: str) -> dict:
    seq = sequence.upper()
    counts = {
        "a_count": seq.count('A'),
        "t_count": seq.count('T'),
        "c_count": seq.count('C'),
        "g_count": seq.count('G'),
    }
    total = sum(counts.values())
    if total > 0:
        counts["gc_content"] = (counts["c_count"] + counts["g_count"]) / total
    else:
        counts["gc_content"] = 0
    return counts

async def get_gene_with_stats(db: AsyncSession, gene_id: int):
    db_gene = await db.get(models.Gene, gene_id)
    if db_gene:
        db_gene.stats = calculate_dna_stats(db_gene.sequence)
    return db_gene

async def get_genes_by_label(db: AsyncSession, label: str):
    result = await db.execute(select(models.Gene).where(models.Gene.label == label))
    return result.scalars().first()

async def get_genes_by_sequence(db: AsyncSession, sequence: str):
    result = await db.execute(select(models.Gene).where(models.Gene.sequence.contains(sequence)))
    return result.scalars().all()

async def delete_gene(db: AsyncSession, gene_id: int):
    db_gene = await db.get(models.Gene, gene_id)
    if db_gene:
        await db.delete(db_gene)
        await db.commit()
    return db_gene

async def update_gene(db:AsyncSession, gene_id:int, gene:schemas):
    db_gene = await db.get(models.Gene, gene_id)
    if db_gene:
        if gene.label:
            existing_gene = await get_genes_by_label(db, label=gene.label)
            if existing_gene and existing_gene.id != gene_id:
                raise ValueError("Gene with this label already exists")
        for key, value in gene.model_dump().items():
            setattr(db_gene, key, value)
        await db.commit()
        await db.refresh(db_gene)
    return db_gene