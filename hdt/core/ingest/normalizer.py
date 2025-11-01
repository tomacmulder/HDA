from __future__ import annotations
from typing import List, Tuple
import hashlib, unicodedata
from ..schema_ingest import RawDocument, CanonicalDocument, Alignment, SpanOp

def _doc_id_from_bytes(b: bytes) -> str:
    return f"doc-{hashlib.sha1(b).hexdigest()[:10]}"

def _is_combining(ch: str) -> bool:
    # Unicode combining marks categories start with "M" (Mn, Mc, Me)
    return unicodedata.category(ch).startswith("M")

def normalize_bytes(raw_bytes: bytes, *, media_type: str = "text/plain", encoding: str = "utf-8") -> Tuple[RawDocument, CanonicalDocument, str]:
    """
    v1 canonicalization:
      - decode bytes with the given encoding (strict)
      - Drop leading UTF-8 BOM if present
      - CRLF/CR -> LF using replace ops
      - NBSP (U+00A0) -> space using replace ops
      - NFC normalization for base+combining sequences (e.g., e + ◌́ -> é)
    """
    orig = raw_bytes.decode(encoding, errors="strict")
    n = len(orig)

    ops: List[SpanOp] = []
    canon_chars: List[str] = []

    i = 0
    cpos = 0
    while i < n:
        ch = orig[i]

        # Drop leading BOM (U+FEFF)
        if i == 0 and ch == "\ufeff":
            ops.append(SpanOp(kind="delete", orig=(i, i + 1), canon=(cpos, cpos)))
            i += 1
            continue

        # Newline normalization first
        if ch == "\r":
            if i + 1 < n and orig[i + 1] == "\n":
                ops.append(SpanOp(kind="replace", orig=(i, i + 2), canon=(cpos, cpos + 1)))
                canon_chars.append("\n"); i += 2; cpos += 1
            else:
                ops.append(SpanOp(kind="replace", orig=(i, i + 1), canon=(cpos, cpos + 1)))
                canon_chars.append("\n"); i += 1; cpos += 1
            continue

        # NBSP -> space
        if ch == "\u00A0":
            ops.append(SpanOp(kind="replace", orig=(i, i + 1), canon=(cpos, cpos + 1)))
            canon_chars.append(" "); i += 1; cpos += 1
            continue

        # Cluster base + following combining marks to allow NFC
        j = i + 1
        while j < n and _is_combining(orig[j]):
            j += 1

        cluster = orig[i:j]
        nfc = unicodedata.normalize("NFC", cluster)

        if nfc == cluster:
            # Emit keeps per-codepoint for precise mapping
            for k in range(i, j):
                ops.append(SpanOp(kind="keep", orig=(k, k + 1), canon=(cpos, cpos + 1)))
                canon_chars.append(orig[k]); cpos += 1
        else:
            # Cluster changed length/content; treat as a single replace
            new_len = len(nfc)
            ops.append(SpanOp(kind="replace", orig=(i, j), canon=(cpos, cpos + new_len)))
            canon_chars.append(nfc); cpos += new_len

        i = j

    canonical_text = "".join(canon_chars)

    raw = RawDocument(
        doc_id=_doc_id_from_bytes(raw_bytes),
        media_type=media_type,
        encoding=encoding,
        bytes_len=len(raw_bytes),
    )
    aln = Alignment(
        ops=ops, encoding=encoding,
        orig_len=len(orig), canon_len=len(canonical_text)
    )
    can = CanonicalDocument(
        doc_id=raw.doc_id,
        canonical_text=canonical_text,
        lang_blocks=[{"start": 0, "end": len(canonical_text), "bcp47": "und", "confidence": 0.0}],
        alignment=aln,
    )
    return raw, can, orig
