from __future__ import annotations
from typing import List
from pydantic import BaseModel, Field

class TopicAssignment(BaseModel):
    AMU_ID: str
    Topic_ID: str
    Topic_Label: str
    Topic_Assign_Confidence: float = Field(ge=0.0, le=1.0)
    Topic_Disambiguators: List[str] = Field(default_factory=list)
