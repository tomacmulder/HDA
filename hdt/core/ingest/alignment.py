from __future__ import annotations
from typing import List, Tuple
from ..schema_ingest import Alignment, SpanOp

class AlignmentIndex:
    """
    Map original decoded char boundaries ? canonical char boundaries,
    and convert canonical spans back to original byte spans.
    """
    def __init__(self, alignment: Alignment, byte_starts: List[int]):
        self.aln = alignment
        self.byte_starts = byte_starts
        self._orig2canon = [0] * (alignment.orig_len + 1)
        self._canon2orig = [0] * (alignment.canon_len + 1)

        for op in alignment.ops:
            o0, o1 = op.orig
            c0, c1 = op.canon
            o_len = o1 - o0
            c_len = c1 - c0

            if op.kind in ("keep",) and o_len == c_len:
                for i in range(o_len + 1):
                    self._orig2canon[o0 + i] = c0 + i
                    self._canon2orig[c0 + i] = o0 + i
            else:
                for i in range(max(o_len, 0) + 1):
                    self._orig2canon[min(o0 + i, self.aln.orig_len)] = c0
                for i in range(max(c_len, 0) + 1):
                    self._canon2orig[min(c0 + i, self.aln.canon_len)] = o0

        for i in range(1, len(self._orig2canon)):
            if self._orig2canon[i] < self._orig2canon[i - 1]:
                self._orig2canon[i] = self._orig2canon[i - 1]
        for i in range(1, len(self._canon2orig)):
            if self._canon2orig[i] < self._canon2orig[i - 1]:
                self._canon2orig[i] = self._canon2orig[i - 1]

    def forward_char(self, orig_char_boundary: int) -> int:
        oc = max(0, min(orig_char_boundary, self.aln.orig_len))
        return self._orig2canon[oc]

    def inverse_char(self, canon_char_boundary: int) -> int:
        cc = max(0, min(canon_char_boundary, self.aln.canon_len))
        return self._canon2orig[cc]

    def inverse_bytes(self, canon_span: Tuple[int, int]) -> Tuple[int, int]:
        c0, c1 = canon_span
        o0 = self.inverse_char(c0)
        o1 = self.inverse_char(c1)
        return self.byte_starts[o0], self.byte_starts[o1]

def compute_byte_starts(orig_text: str, encoding: str) -> List[int]:
    starts = [0]
    acc = 0
    for ch in orig_text:
        acc += len(ch.encode(encoding, errors="strict"))
        starts.append(acc)
    return starts

def replay_ops(orig_text: str, ops: List[SpanOp]) -> str:
    out_parts: List[str] = []
    for op in ops:
        o0, o1 = op.orig
        if op.kind == "keep":
            out_parts.append(orig_text[o0:o1])
        elif op.kind in ("delete", "insert", "replace"):
            out_parts.append("")
    return "".join(out_parts)
