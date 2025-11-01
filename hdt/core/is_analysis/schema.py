from __future__ import annotations
from typing import Literal, Optional, List
from pydantic import BaseModel, Field

# ----- I1 Scaffold -----
EventKindT = Literal["state","process","achievement","accomplishment"]
PredicationT = Literal["state_is","change_delta","membership","definition"]
NegationT = Literal["none","explicit"]
IntensionalityT = Literal["extensional","belief_about_world"]

class ArgumentsModel(BaseModel):
    agent: Optional[str] = None
    patient: Optional[str] = None
    locus: Optional[str] = None
    instrument: Optional[str] = None

class ScaffoldRow(BaseModel):
    AMU_ID: str
    Event_Kind: EventKindT
    Predication: PredicationT
    Arguments: ArgumentsModel = Field(default_factory=ArgumentsModel)
    Negation: NegationT = "none"
    Intensionality: IntensionalityT = "extensional"

# ----- I2 Time/Modality/Scope -----
TimeAxisT = Literal["past","present","future","generic","atemporal"]
TemporalHorizonT = Literal["immediate","short_term","long_term","timeless","none"]
ChangeTenseSignalT = Literal["past_reference","present_trend","future","counterfactual","timeless","none"]
EpistemicModalityT = Literal["certain","hedged","speculative","interrogative","counterfactual"]
EpistemicForceT = Literal["strong","moderate","weak","none"]
ScopeTypeT = Literal["universal","general","local","individual","unspecified"]

class ModalRow(BaseModel):
    Statement_Text_ID: str
    Time_Axis: TimeAxisT = "present"
    Temporal_Horizon: TemporalHorizonT = "none"
    Change_Tense_Signal: ChangeTenseSignalT = "none"
    Epistemic_Modality: EpistemicModalityT = "certain"
    Epistemic_Force: EpistemicForceT = "strong"
    Scope_Type: ScopeTypeT = "unspecified"

# ----- I3 Evidential -----
EvidentialBasisT = Literal["empirical","testimonial","inferential","theoretical","anecdotal","speculative","none"]

class EvidentialRow(BaseModel):
    Statement_Text_ID: str
    Evidential_Basis: EvidentialBasisT = "none"
    Cues: List[str] = Field(default_factory=list)

# ----- I5 Causal skeleton (lite) -----
EdgeKindT = Literal["causes","enables","prevents","correlates"]

class CausalEdge(BaseModel):
    from_id: str
    to_id: str
    kind: EdgeKindT = "causes"
    Mechanism_Role: str = "unspecified"
