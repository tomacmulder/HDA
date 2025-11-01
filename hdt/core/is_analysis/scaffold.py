from __future__ import annotations
from typing import List
import re
from .schema import ScaffoldRow
from ..amu.schema import AMU
from ..segment.spans import Statement

# simple dictionaries / regexes; deterministic and language-agnostic-ish
_CHANGE = re.compile(r"\b(increase|increased|increases|grow|grew|grown|rise|rose|fallen|fall|drop|decline|improve|worsen)\b", re.I)
_STATE_IS = re.compile(r"\b(is|are|was|were|be|been)\b", re.I)
_MEMBERSHIP = re.compile(r"\b(is|are)\s+(an?|the)\b", re.I)
_NEG = re.compile(r"\b(no|not|never|none|no\s+longer)\b", re.I)
_INTENSION = re.compile(r"\b(think|believe|feel|claim|say|report|suggest|hope|guess)\b", re.I)

def build_scaffold(statements: List[Statement], amus: List[AMU]) -> List[ScaffoldRow]:
    # map AMU by statement
    amu_by_stmt = {a.Parent_Statement_ID: a for a in amus if a.AMU_Type == "d_prop"}
    rows: List[ScaffoldRow] = []

    for st in statements:
        a = amu_by_stmt.get(st.id)
        if not a:
            continue
        # Exclude interrogatives for I1 (keep it clean)
        if st.text.strip().endswith("?"):
            continue

        text = st.text
        if _CHANGE.search(text):
            pred = "change_delta"; kind = "process"
        elif _MEMBERSHIP.search(text):
            pred = "membership"; kind = "state"
        elif _STATE_IS.search(text):
            pred = "state_is"; kind = "state"
        else:
            pred = "state_is"; kind = "state"

        neg = "explicit" if _NEG.search(text) else "none"
        inten = "belief_about_world" if _INTENSION.search(text) else "extensional"

        rows.append(ScaffoldRow(
            AMU_ID=a.AMU_ID,
            Event_Kind=kind, Predication=pred,
            Negation=neg, Intensionality=inten
        ))
    return rows
