from __future__ import annotations
from typing import List
import re
from .schema import EvidentialRow
from ..segment.spans import Statement

_PATTERNS = [
    ("empirical",    r"\b(data|measured|observed|experiment|survey|dataset|evidence shows?)\b"),
    ("testimonial",  r"\b(according to|said|stated|reported by|per\s+\w+|per\s+the|per\s+report)\b"),
    ("inferential",  r"\b(therefore|thus|hence|implies|suggests that|so that)\b"),
    ("theoretical",  r"\b(theory|model|axiom|hypothesis|postulate)\b"),
    ("anecdotal",    r"\b(anecdot|story|heard that|someone said)\b"),
    ("speculative",  r"\b(speculate|guess|perhaps|maybe|it\s+seems)\b"),
]

def classify_evidence(statements: List[Statement]) -> List[EvidentialRow]:
    out: List[EvidentialRow] = []
    for st in statements:
        text = st.text.lower()
        basis = "none"
        cues: List[str] = []
        for label, pat in _PATTERNS:
            if re.search(pat, text):
                basis = label
                # collect rough cue
                cues.append(label)
                break
        out.append(EvidentialRow(Statement_Text_ID=st.id, Evidential_Basis=basis, Cues=cues))
    return out
