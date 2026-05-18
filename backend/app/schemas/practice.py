from datetime import datetime

from pydantic import BaseModel, Field


class Keyword(BaseModel):
    text: str
    phonetic: str | None = None
    meaning_cn: str
    example: str | None = None


class PracticeTaskCreateRequest(BaseModel):
    level: int = Field(3, ge=1, le=3)
    category: str = "business"
    scenario_name: str | None = Field(None, min_length=1, max_length=120)
    user_id: int | None = None


class PracticeTaskResponse(BaseModel):
    id: int
    level: int
    category: str
    task_name: str
    cn_sentence: str
    context_cn: str
    keywords: list[Keyword]
    created_at: datetime

    model_config = {"from_attributes": True}


class Mistake(BaseModel):
    type: str
    original: str
    suggestion: str
    explanation_cn: str


class Alternatives(BaseModel):
    polite: str
    neutral: str
    casual: str


class Feedback(BaseModel):
    score: int = Field(..., ge=0, le=100)
    grammar_score: int = Field(..., ge=0, le=100)
    authenticity_score: int = Field(..., ge=0, le=100)
    politeness_score: int = Field(..., ge=0, le=100)
    corrected_sentence: str
    feedback_cn: str
    mistakes: list[Mistake] = []
    alternatives: Alternatives


class AttemptRequest(BaseModel):
    task_id: int
    user_input: str = Field(..., min_length=1, max_length=1000)


class AttemptResponse(BaseModel):
    id: int
    task_id: int
    user_input: str
    score: int
    mastered: bool
    review_due_at: datetime
    feedback: Feedback
    created_at: datetime

    model_config = {"from_attributes": True}


class HintRequest(BaseModel):
    task_id: int


class HintResponse(BaseModel):
    task_id: int
    hints: Alternatives
    explanation_cn: str


class ReviewItem(BaseModel):
    attempt_id: int
    task_id: int
    cn_sentence: str
    user_input: str
    corrected_sentence: str
    score: int
    mastered: bool
    review_due_at: datetime
