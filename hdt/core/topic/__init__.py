from __future__ import annotations
from typing import List, Dict, Any, Optional, Tuple
import re

__all__ = ["assign_topics"]

def _coerce_dict(obj: Any) -> Dict[str, Any]:
    if isinstance(obj, dict): return obj
    for attr in ("model_dump","dict"):
        fn = getattr(obj, attr, None)
        if callable(fn):
            try:
                d = fn()
                if isinstance(d, dict): return d
            except Exception:
                pass
    d = {}
    # AMU-centric fields
    for k in ("AMU_ID","Parent_Statement_ID","Text_Span","Char_Start","Char_End"):
        if hasattr(obj, k): d[k] = getattr(obj, k)
    # Fallback text keys
    for k in ("text","raw","content","Statement_Text","Text_Span"):
        if k not in d and hasattr(obj, k): d[k] = getattr(obj, k)
    return d

def _score_topic(span: str, topic_def: Dict[str, Any]) -> Tuple[float, list]:
    """Simple keyword scorer; returns (confidence, disambiguators_hit)."""
    tl = (span or "").lower()
    kws = [k.lower() for k in topic_def.get("keywords", [])]
    dis = [k.lower() for k in topic_def.get("disambiguators", [])]
    hits = [k for k in kws if re.search(rf"\b{re.escape(k)}\b", tl)]
    dhit = [k for k in dis if re.search(rf"\b{re.escape(k)}\b", tl)]
    if not kws:
        return (0.0, dhit)
    conf = min(0.95, max(0.0, len(hits) / max(1, len(kws))))
    # small lift if disambiguators also present
    if dhit:
        conf = min(0.99, conf + 0.1)
    return (conf, dhit)

def _topics_index(guides: Dict[str, Any]) -> List[Dict[str, Any]]:
    """
    Accepts either:
      - {"topics":[{"id": "...", "label": "...", "keywords":[...], "disambiguators":[...]}]}
      - or {"topic_keywords": {"id_or_label":[kw1,kw2,...], ...}}
    Produces a uniform list of topic dicts.
    """
    if "topics" in guides and isinstance(guides["topics"], list):
        out = []
        for t in guides["topics"]:
            out.append({
                "id": t.get("id") or t.get("topic_id") or (t.get("label","misc").lower().replace(" ","_")),
                "label": t.get("label") or t.get("id") or "misc",
                "keywords": t.get("keywords", []),
                "disambiguators": t.get("disambiguators", []),
            })
        return out
    tk = guides.get("topic_keywords", {})
    out = []
    for k, kws in tk.items():
        out.append({
            "id": str(k),
            "label": str(k),
            "keywords": list(kws or []),
            "disambiguators": [],
        })
    if not out:
        # ultra-minimal default so the step doesn't fail
        out = [
            {"id":"general", "label":"General", "keywords":[], "disambiguators":[]}
        ]
    return out

def assign_topics(amus: List[Any], guides: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
    g = guides or {}
    topics = _topics_index(g)
    min_conf = float(g.get("min_confidence", 0.20))
    rows: List[Dict[str, Any]] = []

    for i, amu in enumerate(amus):
        d = _coerce_dict(amu)
        amu_id = d.get("AMU_ID") or f"A{i+1}"
        span   = d.get("Text_Span") or d.get("text") or ""

        best = ("misc", "Misc", 0.0, [])
        for td in topics:
            conf, dhit = _score_topic(span, td)
            if conf > best[2]:
                best = (td["id"], td["label"], conf, dhit)

        topic_id, topic_label, conf, dhit = best
        if conf < min_conf and topics:
            # fall back to the most generic topic but keep transparency
            topic_id, topic_label = "general", "General"

        rows.append({
            "AMU_ID": amu_id,
            "Topic_ID": topic_id,
            "Topic_Label": topic_label,
            "Topic_Assign_Confidence": round(float(conf), 3),
            "Topic_Disambiguators": dhit,
        })
    return rows
