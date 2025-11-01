from __future__ import annotations
from typing import List
import re
from .schema import ModalRow
from ..segment.spans import Statement

_FUTURE = re.compile(r"\b(will|shall|going to|next|tomorrow|soon)\b", re.I)
_PAST = re.compile(r"\b(yesterday|last\s+(week|month|year|quarter)|ago)\b", re.I)
_COUNTERF = re.compile(r"\b(would|could|should)\b", re.I)
_HEDGED = re.compile(r"\b(might|may|could|perhaps|possibly|likely|appears|suggests)\b", re.I)
_QMARK = re.compile(r"\?\s*$")
_SCOPE_UNI = re.compile(r"\b(all|every|each|always)\b", re.I)
_SCOPE_GEN = re.compile(r"\b(most|usually|generally|often)\b", re.I)
_SCOPE_LOCAL = re.compile(r"\b(locally|in\s+this|here|at\s+our)\b", re.I)
_SCOPE_INDIV = re.compile(r"\b(this|that|a|an)\b", re.I)

def analyze_time_modality(statements: List[Statement]) -> List[ModalRow]:
    out: List[ModalRow] = []
    for st in statements:
        text = st.text

        axis = "present"
        signal = "none"
        if _COUNTERF.search(text):
            axis, signal = "future", "counterfactual"
        elif _FUTURE.search(text):
            axis, signal = "future", "future"
        elif _PAST.search(text):
            axis, signal = "past", "past_reference"
        elif _QMARK.search(text):
            axis, signal = "present", "none"

        # horizon heuristic
        horizon = "none"
        if re.search(r"\b(next|this)\s+(week|month)\b", text, re.I):
            horizon = "short_term"
        elif re.search(r"\b(next|this)\s+(quarter|year)\b", text, re.I):
            horizon = "long_term"

        # epistemic
        if _QMARK.search(text):
            modality, force = "interrogative", "none"
        elif _COUNTERF.search(text):
            modality, force = "counterfactual", "weak"
        elif _HEDGED.search(text):
            modality, force = "hedged", "moderate"
        else:
            modality, force = "certain", "strong"

        # scope
        if _SCOPE_UNI.search(text):
            scope = "universal"
        elif _SCOPE_GEN.search(text):
            scope = "general"
        elif _SCOPE_LOCAL.search(text):
            scope = "local"
        elif _SCOPE_INDIV.search(text):
            scope = "individual"
        else:
            scope = "unspecified"

        out.append(ModalRow(
            Statement_Text_ID=st.id,
            Time_Axis=axis,
            Temporal_Horizon=horizon,
            Change_Tense_Signal=signal,
            Epistemic_Modality=modality,
            Epistemic_Force=force,
            Scope_Type=scope,
        ))
    return out
