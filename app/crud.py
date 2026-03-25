import json
from redis import Redis

from Bio import SeqIO
from io import StringIO

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy import insert
from . import models, schemas

async def get_gene(db: AsyncSession, gene_id: int):
    result = await db.execute(select(models.Gene).where(models.Gene.id == gene_id))
    return result.scalars().first()

async def create_gene(db: AsyncSession, gene: schemas.GeneCreate):
    computed_gc_content = calculate_dna_stats(gene.sequence)["gc_content"]
    db_gene = models.Gene(
        label=gene.label,
        sequence=gene.sequence.replace('\n', ''),
        gc_content=computed_gc_content,
        description=gene.description
    )
    db.add(db_gene)
    await db.commit()
    await db.refresh(db_gene)
    return db_gene

def calculate_dna_stats(sequence: str) -> dict:
    seq = sequence.replace('\n', '').upper()
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
    result = await db.execute(select(models.Gene).where(models.Gene.sequence.contains(sequence.upper())))
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

async def bulk_create_genes_from_fasta(db: AsyncSession, fasta_content: str):
    fasta_io = StringIO(fasta_content)
    total_count = 0
    new_genes_data = []
    for record in SeqIO.parse(fasta_io, "fasta"):
        label = record.id
        sequence = str(record.seq).upper()
        description = record.description
        computed_gc_content = calculate_dna_stats(sequence)["gc_content"]

        gene_dict = {
            "label": label,
            "sequence": sequence,
            "gc_content": computed_gc_content,
            "description": description
        }
        new_genes_data.append(gene_dict)
        total_count += 1 
        if len(new_genes_data) >= 100:
            await db.execute(insert(models.Gene),new_genes_data)
            await db.commit()
            new_genes_data = []

    if new_genes_data:
        await db.execute(insert(models.Gene),new_genes_data)
        await db.commit()
    
    return total_count

def serialize_gene_meta(gene: models.Gene) -> str:
    return json.dumps({
        "id": gene.id,
        "label": gene.label,
        "gc_content": gene.gc_content,
        "description": gene.description[:100] if gene.description else None,
    })

async def get_gene_metadata(db: AsyncSession, redis: Redis, gene_id: int):
    cache_key = "genes_meta_hash"
    
    cached_data = await redis.hget(cache_key, str(gene_id))
    if cached_data:
        return json.loads(cached_data)

    result = await db.execute(select(models.Gene).where(models.Gene.id == gene_id))
    gene = result.scalar_one_or_none()

    if gene:
        meta_json = serialize_gene_meta(gene)
        await redis.hset(cache_key, str(gene.id), meta_json)
        return json.loads(meta_json)
    
    return None

async def warmup_gene_cache(db: AsyncSession, redis: Redis, limit=10):
    result = await db.execute(select(models.Gene).limit(limit))
    genes = result.scalars().all()
    
    if genes:
        mapping = {str(g.id): serialize_gene_meta(g) for g in genes}
        await redis.hset("genes_meta_hash", mapping=mapping)
        return len(genes)
    return 0