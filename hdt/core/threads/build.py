from __future__ import annotations
from typing import List, Dict, Tuple
import re
from .schema import ThreadRow
from ..segment.spans import Statement
from ..amu.schema import AMU
from ..topic.schema import TopicAssignment

_PHATIC = (
    r"\bokay\b", r"\bok\b", r"\bum\b", r"\buh\b", r"\byou know\b", r"\blikely\b",
    r"\bi think\b", r"\bi feel\b", r"\bwell,\b", r"\bthanks\b", r"\bthank you\b"
)
_PHATIC_RE = re.compile("|".join(_PHATIC), flags=re.IGNORECASE)

def _eligibility(text: str) -> float:
    if _PHATIC_RE.search(text):
        return 0.1
    # short fragments are weak anchors
    base = 0.8 if len(text.strip()) >= 8 else 0.5
    # de-emphasize trailing questions as anchors
    if text.strip().endswith("?"):
        base -= 0.2
    return max(0.0, min(1.0, base))

def _thread_id(doc_id: str, idx: int) -> str:
    return f"{doc_id}_T{idx+1}"

def build_threads(statements: List[Statement], amus: List[AMU], topics: List[TopicAssignment]) -> List[ThreadRow]:
    # map statement -> topic label (one AMU per statement in v1)
    topic_by_stmt: Dict[str, str] = {}
    for a, t in zip(amus, topics):
        topic_by_stmt[a.Parent_Statement_ID] = t.Topic_Label

    rows: List[ThreadRow] = []
    if not statements:
        return rows

    # contiguous threads by topic label
    cur_topic = None
    cur_thread_index = -1
    cur_members: List[Tuple[Statement, float]] = []

    def flush_thread():
        nonlocal rows, cur_members, cur_thread_index
        if not cur_members:
            return
        # pick best anchor by eligibility
        anchor_idx = max(range(len(cur_members)), key=lambda i: cur_members[i][1])
        for i, (st, score) in enumerate(cur_members):
            rows.append(ThreadRow(
                Statement_Text_ID=st.id,
                Thread_ID=_thread_id(st.id.split("_S", 1)[0], cur_thread_index),
                Thread_Role="anchor" if i == anchor_idx else "support",
                Anchor_Eligibility_Score=score
            ))
        cur_members = []

    for st in statements:
        label = topic_by_stmt.get(st.id, "general")
        if label != cur_topic:
            # new thread
            flush_thread()
            cur_thread_index += 1
            cur_topic = label
        cur_members.append((st, _eligibility(st.text)))

    flush_thread()
    return rows
