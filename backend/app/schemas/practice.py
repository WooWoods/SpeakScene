from datetime import datetime
from typing import Literal

from pydantic import BaseModel, Field


class ScenarioPhrase(BaseModel):
    en: str
    cn: str
    usage_note_cn: str = ""
    tone: str = "neutral"
    favorite_candidate: bool = True


class ScenarioStartRequest(BaseModel):
    level: int = Field(3, ge=1, le=3)
    category: str = "business"
    scenario_name: str | None = Field(None, min_length=1, max_length=160)
    user_id: int | None = None


class ConversationTurnResponse(BaseModel):
    id: int
    session_id: int
    speaker: Literal["system", "user"]
    text_en: str
    text_cn: str | None = None
    input_mode: Literal["system", "voice", "typing", "handwriting"]
    created_at: datetime

    model_config = {"from_attributes": True}


class ConversationEvaluation(BaseModel):
    overall_score: int = Field(..., ge=0, le=100)
    vocabulary_score: int = Field(..., ge=0, le=100)
    grammar_score: int = Field(..., ge=0, le=100)
    authenticity_score: int = Field(..., ge=0, le=100)
    fluency_score: int = Field(..., ge=0, le=100)
    feedback_cn: str
    strengths: list[str] = []
    improvements: list[str] = []
    suggested_phrases: list[ScenarioPhrase] = []


class ScenarioSessionResponse(BaseModel):
    id: int
    user_id: int | None = None
    level: int
    category: str
    scenario_name: str
    scenario_context_cn: str
    starter_en: str
    starter_cn: str
    phrases: list[ScenarioPhrase]
    status: Literal["active", "completed"]
    evaluation: ConversationEvaluation | None = None
    turns: list[ConversationTurnResponse] = []
    created_at: datetime
    completed_at: datetime | None = None

    model_config = {"from_attributes": True}


class TurnCreateRequest(BaseModel):
    text_en: str = Field(..., min_length=1, max_length=1500)
    input_mode: Literal["voice", "typing", "handwriting"] = "typing"


class TurnCreateResponse(BaseModel):
    user_turn: ConversationTurnResponse
    system_turn: ConversationTurnResponse
    session: ScenarioSessionResponse


class SessionCompleteResponse(BaseModel):
    session_id: int
    status: Literal["completed"]
    evaluation: ConversationEvaluation


class FavoriteCreateRequest(BaseModel):
    user_id: int | None = None
    category: str = Field(..., min_length=1, max_length=80)
    scenario_name: str = Field(..., min_length=1, max_length=160)
    phrase_en: str = Field(..., min_length=1, max_length=1000)
    phrase_cn: str = Field(..., min_length=1, max_length=1000)
    usage_note_cn: str = ""


class FavoriteResponse(BaseModel):
    id: int
    user_id: int | None = None
    category: str
    scenario_name: str
    phrase_en: str
    phrase_cn: str
    usage_note_cn: str
    created_at: datetime

    model_config = {"from_attributes": True}


class FavoritesByCategory(BaseModel):
    category: str
    items: list[FavoriteResponse]
