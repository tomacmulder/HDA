from __future__ import annotations
from typing import Any, Dict, List, Tuple
from collections import defaultdict

def _norm_stmt_id(s: Dict[str, Any]) -> str:
    return s.get("id") or s.get("statement_id") or s.get("sid") or ""

def _stmt_text(s: Dict[str, Any]) -> str:
    return s.get("text") or s.get("content") or s.get("span_text") or ""

def _link_src(e: Dict[str, Any]) -> str | None:
    return e.get("src") or e.get("source") or e.get("source_id") or e.get("from") or e.get("a")

def _link_dst(e: Dict[str, Any]) -> str | None:
    return e.get("dst") or e.get("target") or e.get("target_id") or e.get("to") or e.get("b")

def _thread_members(t: Dict[str, Any]) -> List[str]:
    return (
        t.get("members")
        or t.get("statement_ids")
        or t.get("ids")
        or t.get("statements")
        or []
    )

def _trunc(s: str, n: int = 120) -> str:
    s = s.replace("\r", " ").replace("\n", " ").strip()
    return s if len(s) <= n else s[:n-1] + "…"

def synthesize_canon(statements: List[Any], links: List[Any], threads: List[Any]) -> Dict[str, Any]:
    # Normalize statements
    stmt_rows: List[Dict[str, Any]] = []
    id_to_text: Dict[str, str] = {}
    for raw in statements or []:
        s = raw.model_dump() if hasattr(raw, "model_dump") else raw
        sid = _norm_stmt_id(s)
        txt = _stmt_text(s) or ""
        id_to_text[sid] = txt
        stmt_rows.append({
            "id": sid,
            "len": len(txt),
            "preview": _trunc(txt, 160),
        })

    # Link degrees
    indeg = defaultdict(int)
    outdeg = defaultdict(int)
    edges: List[Tuple[str, str]] = []
    for raw in links or []:
        e = raw.model_dump() if hasattr(raw, "model_dump") else raw
        a, b = _link_src(e), _link_dst(e)
        if a and b:
            edges.append((a, b))
            outdeg[a] += 1
            indeg[b] += 1

    deg_rows: List[Dict[str, Any]] = []
    ids = list({r["id"] for r in stmt_rows if r["id"]})
    for sid in ids:
        deg_rows.append({
            "id": sid,
            "in": indeg[sid],
            "out": outdeg[sid],
            "deg": indeg[sid] + outdeg[sid],
        })
    deg_rows.sort(key=lambda r: (-r["deg"], r["id"]))

    # Threads summary
    thread_rows: List[Dict[str, Any]] = []
    for raw in threads or []:
        t = raw.model_dump() if hasattr(raw, "model_dump") else raw
        mids = [m for m in _thread_members(t) if isinstance(m, str)]
        thread_rows.append({
            "id": t.get("id") or t.get("thread_id") or t.get("tid") or f"thread_{len(thread_rows)+1}",
            "size": len(mids),
            "members": mids[:20],  # cap the list to keep file small
        })
    thread_rows.sort(key=lambda r: (-r["size"], r["id"]))

    # Build canon
    canon = {
        "source": "local_synth",
        "stats": {
            "statements": len(stmt_rows),
            "links": len(edges),
            "threads": len(thread_rows),
        },
        "statements_head": stmt_rows[:20],
        "top_degree_nodes": deg_rows[:20],
        "threads_head": thread_rows[:20],
    }
    return canon
