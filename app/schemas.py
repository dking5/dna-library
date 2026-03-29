from pydantic import BaseModel, Field, ConfigDict, computed_field
from typing import Optional
from .utils import get_reverse_complement

class GeneStats(BaseModel):
    a_count: int
    t_count: int
    c_count: int
    g_count: int
    gc_content: float

class GeneBase(BaseModel):
    label: str = Field(..., min_length=3)
    sequence: str = Field(..., pattern=r"^[ATCGNatcgn\s]+$")
    description: Optional[str] = None

class GeneCreate(GeneBase):
    pass

class Gene(GeneBase):
    id: int
    gc_content: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)

    @computed_field
    @property
    def reverse_complement(self) -> str:
        return get_reverse_complement(self.sequence)



