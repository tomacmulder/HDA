from __future__ import annotations
from typing import List, Literal
from pydantic import BaseModel, Field

RelationStrength = Literal["weak", "moderate", "strong"]

class LinkRow(BaseModel):
    Statement_Text_ID: str
    Supports_IDs: List[str] = Field(default_factory=list)
    Opposes_IDs: List[str] = Field(default_factory=list)
    References_IDs: List[str] = Field(default_factory=list)
    Relation_Cues: List[str] = Field(default_factory=list)
    Relation_Strength: RelationStrength = "moderate"
