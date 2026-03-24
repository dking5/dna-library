from pydantic import BaseModel, Field, ConfigDict
from typing import Optional

class GeneStats(BaseModel):
    a_count: int
    t_count: int
    c_count: int
    g_count: int
    gc_content: float

class GeneBase(BaseModel):
    label: str = Field(..., min_length=3)
    sequence: str = Field(..., pattern="^[ATCGNatcgn\s]+$")
    description: Optional[str] = None

class GeneCreate(GeneBase):
    pass

class Gene(GeneBase):
    id: int
    gc_content: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)