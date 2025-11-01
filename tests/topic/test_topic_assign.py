from __future__ import annotations
from hdt.core.amu.schema import AMU
from hdt.core.topic.assign import assign_topics

def test_simple_finance_detection():
    a = AMU(
        AMU_ID="X@0-12",
        Parent_Statement_ID="X",
        Text_Span="Revenue increased by 10%.",
        Char_Start=0, Char_End=24,
    )
    ta = assign_topics([a])[0]
    assert ta.Topic_Label in {"finance", "general"}
    assert ta.Topic_Assign_Confidence >= 0.4
