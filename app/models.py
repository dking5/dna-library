from sqlalchemy import Column, Integer, String, DateTime
from sqlalchemy.sql import func
from .database import Base

class Gene(Base):
    __tablename__ = "genes" 

    id = Column(Integer, primary_key=True, index=True)
    label = Column(String, index=True)
    sequence = Column(String)
    created_at = Column(DateTime(timezone=True), server_default=func.now())