from __future__ import annotations
from pydantic import BaseModel, Field

class Span(BaseModel):
    start: int = Field(ge=0)
    end: int = Field(ge=0)

    def clamp(self, n: int) -> "Span":
        s = max(0, min(self.start, n))
        e = max(s, min(self.end, n))
        return Span(start=s, end=e)

def trim_span(text: str, span: Span) -> Span:
    s, e = span.start, span.end
    while s < e and text[s].isspace():
        s += 1
    while e > s and text[e-1].isspace():
        e -= 1
    return Span(start=s, end=e)

class Statement(BaseModel):
    id: str
    start: int
    end: int
    text: str
