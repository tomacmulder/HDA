from __future__ import annotations
from typing import Literal, List
from pydantic import BaseModel, Field

AMUType = Literal["d_prop", "n_prop", "attitude", "phatic"]

class AMU(BaseModel):
    AMU_ID: str
    Parent_Statement_ID: str
    Text_Span: str
    Char_Start: int = Field(ge=0)
    Char_End: int = Field(ge=0)
    AMU_Type: AMUType = "d_prop"
    Topic_Candidates: List[str] = Field(default_factory=list)
    Topic_Confidence: float = 0.0
