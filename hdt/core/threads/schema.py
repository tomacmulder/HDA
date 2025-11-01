from __future__ import annotations
from pydantic import BaseModel, Field

class ThreadRow(BaseModel):
    Statement_Text_ID: str
    Thread_ID: str
    Thread_Role: str  # "anchor" | "support"
    Anchor_Eligibility_Score: float = Field(ge=0.0, le=1.0)
