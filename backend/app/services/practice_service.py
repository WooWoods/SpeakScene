from datetime import datetime, timedelta

from sqlalchemy.orm import Session, joinedload

from app.models.practice import PracticeAttempt, PracticeTask
from app.schemas.practice import (
    AttemptResponse,
    HintResponse,
    Keyword,
    PracticeTaskCreateRequest,
    ReviewItem,
)
from app.services.ai_client import GeneratedTask, get_ai_client


def _model_to_generated_task(task: PracticeTask) -> GeneratedTask:
    return GeneratedTask(
        level=task.level,
        category=task.category,
        task_name=task.task_name,
        cn_sentence=task.cn_sentence,
        context_cn=task.context_cn,
        keywords=[Keyword.model_validate(keyword) for keyword in task.keywords],
    )


async def generate_task(db: Session, payload: PracticeTaskCreateRequest) -> PracticeTask:
    ai_client = get_ai_client()
    generated = await ai_client.generate_task(payload.level, payload.category, payload.scenario_name)
    task = PracticeTask(
        user_id=payload.user_id,
        level=generated.level,
        category=generated.category,
        task_name=generated.task_name,
        cn_sentence=generated.cn_sentence,
        context_cn=generated.context_cn,
        keywords=[keyword.model_dump() for keyword in generated.keywords],
    )
    db.add(task)
    db.commit()
    db.refresh(task)
    return task


async def submit_answer(db: Session, task: PracticeTask, user_input: str) -> PracticeAttempt:
    ai_client = get_ai_client()
    feedback = await ai_client.evaluate_answer(_model_to_generated_task(task), user_input)
    review_delay = timedelta(days=7) if feedback.score >= 90 else timedelta(days=1)
    attempt = PracticeAttempt(
        task_id=task.id,
        user_input=user_input,
        feedback=feedback.model_dump(),
        score=feedback.score,
        mastered=feedback.score >= 90,
        review_due_at=datetime.utcnow() + review_delay,
    )
    db.add(attempt)
    db.commit()
    db.refresh(attempt)
    return attempt


async def get_hints(db: Session, task: PracticeTask) -> HintResponse:
    ai_client = get_ai_client()
    hints, explanation_cn = await ai_client.generate_hints(_model_to_generated_task(task))
    return HintResponse(task_id=task.id, hints=hints, explanation_cn=explanation_cn)


def list_attempts(db: Session, limit: int = 20) -> list[AttemptResponse]:
    attempts = (
        db.query(PracticeAttempt)
        .order_by(PracticeAttempt.created_at.desc())
        .limit(limit)
        .all()
    )
    return [AttemptResponse.model_validate(attempt) for attempt in attempts]


def list_due_reviews(db: Session, limit: int = 20) -> list[ReviewItem]:
    attempts = (
        db.query(PracticeAttempt)
        .options(joinedload(PracticeAttempt.task))
        .filter(PracticeAttempt.mastered.is_(False))
        .filter(PracticeAttempt.review_due_at <= datetime.utcnow())
        .order_by(PracticeAttempt.review_due_at.asc())
        .limit(limit)
        .all()
    )
    return [
        ReviewItem(
            attempt_id=attempt.id,
            task_id=attempt.task_id,
            cn_sentence=attempt.task.cn_sentence,
            user_input=attempt.user_input,
            corrected_sentence=attempt.feedback["corrected_sentence"],
            score=attempt.score,
            mastered=attempt.mastered,
            review_due_at=attempt.review_due_at,
        )
        for attempt in attempts
    ]


def mark_attempt_mastered(db: Session, attempt_id: int) -> PracticeAttempt | None:
    attempt = db.get(PracticeAttempt, attempt_id)
    if attempt is None:
        return None
    attempt.mastered = True
    attempt.review_due_at = datetime.utcnow() + timedelta(days=30)
    db.commit()
    db.refresh(attempt)
    return attempt
