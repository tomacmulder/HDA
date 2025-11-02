from __future__ import annotations
from typing import List, Dict, Any
import json, re

def _lower_in(text: str, needles: list[str], ci: bool) -> bool:
    if not needles: return False
    if ci: 
        t = text.lower()
        return any(n.lower() in t for n in needles)
    return any(n in text for n in needles)

def _split_text(t: str, max_len: int, hard: list[str], soft: list[str]) -> List[str]:
    # first, hard delimiters
    parts = [t]
    for d in hard or []:
        tmp = []
        for p in parts:
            tmp.extend(p.split(d))
        parts = tmp
    # then, soft delimiters (keep them attached to right side)
    out: List[str] = []
    for p in parts:
        chunk = p
        for d in soft or []:
            chunk = chunk.replace(d, d.strip() + "|||SOFT|||")
        out.extend([x for x in chunk.split("|||SOFT|||") if x])
    # length fallback: if too long, approximate sentence split
    final: List[str] = []
    for x in out:
        if len(x) <= max_len:
            final.append(x.strip())
        else:
            # split by sentences
            for s in re.split(r"(?<=[.!?])\s+", x):
                s = s.strip()
                if s:
                    final.append(s)
    return [x for x in final if x]

def amuize(statements: List[Dict[str, Any]], controls: Any) -> List[Dict[str, Any]]:
    guide = controls.get_guide("amu_rules") if hasattr(controls, "get_guide") else None
    rules = guide or {}
    split = rules.get("split", {})
    classify = rules.get("classify", {})
    max_len = int(split.get("max_len", 280))
    hard = split.get("hard_delims", [])
    soft = split.get("soft_delims", [])
    ci = bool(classify.get("case_insensitive", True))

    norm = classify.get("normative_markers", [])
    att  = classify.get("attitude_markers", [])
    ph   = classify.get("phatic_markers", [])

    rows: List[Dict[str, Any]] = []
    for st in statements:
        doc_title = st.get("Document_Title","doc")
        sid = st.get("Statement_Text_ID")
        base_start = int(st.get("Char_Start", 0))
        text = st.get("Statement_Text","")
        chunks = _split_text(text, max_len, hard, soft)
        for i, span in enumerate(chunks, start=1):
            # find local char offsets (best-effort first occurrence; if repeated substrings, uses first)
            # we still keep the statement's absolute Char_Start/End to derive doc-level offsets
            rel = text.find(span)
            amu_start = base_start + (rel if rel >= 0 else 0)
            amu_end   = amu_start + len(span)

            # classify
            if _lower_in(span, ph, ci):
                typ = "phatic"
            elif _lower_in(span, att, ci):
                typ = "attitude"
            elif _lower_in(span, norm, ci):
                typ = "n_prop"
            else:
                typ = "d_prop"

            rows.append({
                "AMU_ID": f"{sid}_A{i}",
                "Parent_Statement_ID": sid,
                "Text_Span": span.strip(),
                "Char_Start": amu_start,
                "Char_End": amu_end,
                "AMU_Type": typ,
                "Topic_Candidates": json.dumps([]),
                "Topic_Confidence": 0.0
            })
    return rows
