from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
from typing import List, Dict, Any, Optional
import re

@dataclass
class Segment:
    segment_id: str
    char_start: int
    char_end: int
    text: str
    speaker: Optional[str] = None

def _read_text(path: Path) -> str:
    raw = path.read_bytes()
    if raw.startswith(b"\xef\xbb\xbf"): raw = raw[3:]
    return raw.decode("utf-8", "ignore")

def _split_blocks(txt: str, min_len: int, max_len: int, split_on_blank: bool) -> List[tuple[int,int,str]]:
    parts: List[tuple[int,int,str]] = []
    if split_on_blank:
        cursor = 0
        for m in re.finditer(r"(?:\r?\n){2,}", txt):
            start, end = cursor, m.start()
            block = txt[start:end].strip()
            if block:
                parts.append((start, end, block))
            cursor = m.end()
        tail = txt[cursor:].strip()
        if tail:
            parts.append((cursor, len(txt), tail))
    else:
        parts = [(0, len(txt), txt.strip())]

    out: List[tuple[int,int,str]] = []
    sent_re = re.compile(r"(?<=[.!?])\s+")
    for (s, e, block) in parts:
        if max_len and len(block) > max_len:
            local = txt[s:e]
            offset = s
            last = 0
            for m in sent_re.finditer(local):
                seg = local[last:m.end()].strip()
                if seg:
                    g_start, g_end = offset + last, offset + m.end()
                    out.append((g_start, g_end, seg))
                last = m.end()
            tail = local[last:].strip()
            if tail:
                out.append((offset + last, offset + len(local), tail))
        else:
            out.append((s, e, block))
    return [(s,e,t) for (s,e,t) in out if len(t) >= min_len]

def _maybe_extract_speaker(text: str, pattern: Optional[str]) -> tuple[Optional[str], str]:
    if not pattern:
        return None, text
    m = re.match(pattern, text)
    if m:
        sp = m.group(1).strip()
        rest = text[m.end():].lstrip()
        return (sp, rest if rest else text)
    return None, text

def segment_path(path: str | Path, controls: Any) -> List[Dict[str, Any]]:
    """
    Reads rules from guides: segmentation_rules.json
    {
      "split_on_blank": true, "min_len": 8, "max_len": 600,
      "speaker_pattern": "^(?:([A-Z][a-z]+|[A-Z]):)\\s+"
    }
    """
    guide = None
    if hasattr(controls, "get_guide"):
        guide = controls.get_guide("segmentation_rules")
    if guide is None and hasattr(controls, "get"):
        guide = controls.get("guides.segmentation_rules", {})

    rules = guide or {}
    split_on_blank = bool(rules.get("split_on_blank", True))
    min_len = int(rules.get("min_len", 8))
    max_len = int(rules.get("max_len", 600))
    speaker_pattern = rules.get("speaker_pattern")

    p = Path(path)
    doc_title = p.stem
    txt = _read_text(p)
    spans = _split_blocks(txt, min_len=min_len, max_len=max_len, split_on_blank=split_on_blank)

    rows: List[Dict[str, Any]] = []
    for i, (s, e, t) in enumerate(spans, start=1):
        speaker, cleaned = _maybe_extract_speaker(t, speaker_pattern)
        rows.append({
            # v1 structural contract fields
            "Document_Title": doc_title,
            "Order_Index": i,
            "Statement_Text_ID": f"{doc_title}_S{i}",
            "Statement_Text": cleaned,
            "Speaker_ID": speaker or "",
            "Timestamp_Start": "",
            "Timestamp_End": "",

            # precise offsets (extra but helpful downstream)
            "Char_Start": s,
            "Char_End": e
        })
    return rows
