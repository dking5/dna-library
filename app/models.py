from sqlalchemy import Column, Float, Integer, String, DateTime, Index
from sqlalchemy.sql import func
from pgvector.sqlalchemy import Vector
from .database import Base

class Gene(Base):
    __tablename__ = "genes" 

    id = Column(Integer, primary_key=True, index=True)
    label = Column(String, index=True)
    sequence = Column(String)
    gc_content = Column(Float, nullable=True, index=True)
    description = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    embedding = Column(Vector(3), nullable=True)
    
    __table_args__ = (
        Index(
            "idx_gene_sequence_trgm",
            "sequence",
            postgresql_using="gin",
            postgresql_ops={"sequence": "gin_trgm_ops"},
        ),
    )