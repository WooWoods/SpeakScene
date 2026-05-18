from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.practice import PracticeTask
from app.schemas.practice import (
    AttemptRequest,
    AttemptResponse,
    HintRequest,
    HintResponse,
    PracticeTaskCreateRequest,
    PracticeTaskResponse,
    ReviewItem,
)
from app.services.practice_service import (
    generate_task,
    get_hints,
    list_attempts,
    list_due_reviews,
    mark_attempt_mastered,
    submit_answer,
)

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.post("/tasks/generate", response_model=PracticeTaskResponse)
async def create_task(payload: PracticeTaskCreateRequest, db: Session = Depends(get_db)) -> PracticeTask:
    return await generate_task(db, payload)


@router.post("/attempts/submit", response_model=AttemptResponse)
async def create_attempt(payload: AttemptRequest, db: Session = Depends(get_db)) -> AttemptResponse:
    task = db.get(PracticeTask, payload.task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Practice task not found")
    attempt = await submit_answer(db, task, payload.user_input)
    return AttemptResponse.model_validate(attempt)


@router.post("/hints", response_model=HintResponse)
async def create_hints(payload: HintRequest, db: Session = Depends(get_db)) -> HintResponse:
    task = db.get(PracticeTask, payload.task_id)
    if task is None:
        raise HTTPException(status_code=404, detail="Practice task not found")
    return await get_hints(db, task)


@router.get("/history", response_model=list[AttemptResponse])
def history(limit: int = 20, db: Session = Depends(get_db)) -> list[AttemptResponse]:
    return list_attempts(db, limit)


@router.get("/review/due", response_model=list[ReviewItem])
def due_reviews(limit: int = 20, db: Session = Depends(get_db)) -> list[ReviewItem]:
    return list_due_reviews(db, limit)


@router.post("/review/{attempt_id}/mastered", response_model=AttemptResponse)
def mark_mastered(attempt_id: int, db: Session = Depends(get_db)) -> AttemptResponse:
    attempt = mark_attempt_mastered(db, attempt_id)
    if attempt is None:
        raise HTTPException(status_code=404, detail="Practice attempt not found")
    return AttemptResponse.model_validate(attempt)
