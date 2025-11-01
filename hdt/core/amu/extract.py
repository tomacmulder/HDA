from __future__ import annotations
from typing import List
from .schema import AMU
from ..segment.spans import Statement

def _amu_id(stmt_id: str, start: int, end: int) -> str:
    return f"{stmt_id}@{start}-{end}"

def extract_amus(statements: List[Statement]) -> List[AMU]:
    """
    v1: one AMU per statement (fully extractive). Later we can refine to intra-sentence clauses.
    """
    amus: List[AMU] = []
    for st in statements:
        amus.append(AMU(
            AMU_ID=_amu_id(st.id, st.start, st.end),
            Parent_Statement_ID=st.id,
            Text_Span=st.text,
            Char_Start=st.start,
            Char_End=st.end,
            AMU_Type="d_prop",
            Topic_Candidates=[],
            Topic_Confidence=0.0,
        ))
    return amus
