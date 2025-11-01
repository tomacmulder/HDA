from __future__ import annotations
from typing import List, Dict, Tuple
import re
from .schema import LinkRow
from ..segment.spans import Statement
from ..threads.schema import ThreadRow

# Cues (lowercased). Keep small & deterministic; extend later.
_SUPPORT_STRONG = ("therefore", "thus", "hence", "as a result", "consequently")
_SUPPORT_MODERATE = ("because", "since", "due to", "thereby", "so that", "so ")
_OPPOSE_STRONG = ("however", "nevertheless", "nonetheless", "in contrast")
_OPPOSE_MODERATE = ("but ", "though ", "although", "yet ")
_REFERENCE = ("see", "as noted", "according to", "as per", "per ", "refer", "reference", "cf.")

def _match_any(text: str, keys: Tuple[str, ...]) -> List[str]:
    t = text.lower()
    hits = [k.strip() for k in keys if k in t]
    return list(dict.fromkeys(hits))  # unique & preserve order

def extract_links(statements: List[Statement], threads: List[ThreadRow]) -> List[LinkRow]:
    """For each statement, link to the immediately prior statement in the same thread.
    If no prior-in-thread exists but we detect explicit cues (strong support/oppose or reference),
    fall back to the immediately previous global statement (cross-topic).
    """
    # Order statements by start offset
    stmts_sorted = sorted(statements, key=lambda s: s.start)
    idx_by_id: Dict[str, int] = {s.id: i for i, s in enumerate(stmts_sorted)}
    thread_of: Dict[str, str] = {tr.Statement_Text_ID: tr.Thread_ID for tr in threads}

    last_in_thread: Dict[str, str] = {}
    rows: List[LinkRow] = []

    for i, st in enumerate(stmts_sorted):
        tid = thread_of.get(st.id)
        cues: List[str] = []
        supports: List[str] = []
        opposes: List[str] = []
        refs: List[str] = []
        strength = "moderate"

        text = st.text
        # Detect cues first
        s_strong = _match_any(text, _SUPPORT_STRONG)
        s_mod   = _match_any(text, _SUPPORT_MODERATE) if not s_strong else []
        o_strong = _match_any(text, _OPPOSE_STRONG)
        o_mod    = _match_any(text, _OPPOSE_MODERATE) if not o_strong else []
        r_hits   = _match_any(text, _REFERENCE)

        # Choose candidate predecessor
        prev_in_thread = last_in_thread.get(tid) if tid is not None else None
        prev_global = stmts_sorted[i-1].id if i > 0 else None

        target_for_support_oppose = prev_in_thread or None
        target_for_reference = prev_in_thread or None

        # If no prior-in-thread, allow cross-topic fallback when explicit cues exist
        if prev_in_thread is None:
            if prev_global and (s_strong or o_strong or r_hits):
                target_for_support_oppose = target_for_support_oppose or prev_global
                target_for_reference = target_for_reference or prev_global

        # Apply links in priority order
        if s_strong and target_for_support_oppose:
            supports.append(target_for_support_oppose); cues += s_strong; strength = "strong"
        elif s_mod and target_for_support_oppose:
            supports.append(target_for_support_oppose); cues += s_mod; strength = "moderate"

        if o_strong and target_for_support_oppose:
            opposes.append(target_for_support_oppose); cues += o_strong; strength = "strong"
        elif o_mod and target_for_support_oppose:
            opposes.append(target_for_support_oppose); cues += o_mod; strength = "moderate"

        if r_hits and not (supports or opposes) and target_for_reference:
            refs.append(target_for_reference); cues += r_hits; strength = "weak"

        # Record row (dedup + no self links)
        sup = sorted(set(i for i in supports if i != st.id))
        opp = sorted(set(i for i in opposes if i != st.id))
        ref = sorted(set(i for i in refs if i != st.id))
        rows.append(LinkRow(
            Statement_Text_ID=st.id,
            Supports_IDs=sup,
            Opposes_IDs=opp,
            References_IDs=ref,
            Relation_Cues=cues,
            Relation_Strength=strength,
        ))

        # Update last in thread
        if tid is not None:
            last_in_thread[tid] = st.id

    return rows
