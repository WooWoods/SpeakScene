from datetime import datetime

from sqlalchemy.orm import Session, joinedload

from app.models.practice import ConversationTurn, FavoriteExpression, ScenarioSession
from app.schemas.practice import (
    ConversationEvaluation,
    FavoriteCreateRequest,
    FavoriteResponse,
    FavoritesByCategory,
    ScenarioPhrase,
    ScenarioSessionResponse,
    ScenarioStartRequest,
    TurnCreateRequest,
)
from app.services.ai_client import GeneratedScenario, get_ai_client


def _session_to_generated(session: ScenarioSession) -> GeneratedScenario:
    return GeneratedScenario(
        level=session.level,
        category=session.category,
        scenario_name=session.scenario_name,
        scenario_context_cn=session.scenario_context_cn,
        starter_en=session.starter_en,
        starter_cn=session.starter_cn,
        phrases=[ScenarioPhrase.model_validate(phrase) for phrase in session.phrases],
    )


def _session_response(session: ScenarioSession) -> ScenarioSessionResponse:
    return ScenarioSessionResponse.model_validate(session)


async def start_scenario(db: Session, payload: ScenarioStartRequest) -> ScenarioSession:
    ai_client = get_ai_client()
    generated = await ai_client.generate_scenario(payload.level, payload.category, payload.scenario_name)
    session = ScenarioSession(
        user_id=payload.user_id,
        level=generated.level,
        category=generated.category,
        scenario_name=generated.scenario_name,
        scenario_context_cn=generated.scenario_context_cn,
        starter_en=generated.starter_en,
        starter_cn=generated.starter_cn,
        phrases=[phrase.model_dump() for phrase in generated.phrases],
        status="active",
    )
    db.add(session)
    db.flush()
    db.add(
        ConversationTurn(
            session_id=session.id,
            speaker="system",
            text_en=generated.starter_en,
            text_cn=generated.starter_cn,
            input_mode="system",
        )
    )
    db.commit()
    db.refresh(session)
    return get_session(db, session.id) or session


async def add_user_turn(
    db: Session,
    session: ScenarioSession,
    payload: TurnCreateRequest,
) -> tuple[ConversationTurn, ConversationTurn, ScenarioSessionResponse]:
    if session.status == "completed":
        raise ValueError("Session is already completed")

    user_turn = ConversationTurn(
        session_id=session.id,
        speaker="user",
        text_en=payload.text_en.strip(),
        input_mode=payload.input_mode,
    )
    db.add(user_turn)
    db.flush()

    user_turns_count = (
        db.query(ConversationTurn)
        .filter(ConversationTurn.session_id == session.id)
        .filter(ConversationTurn.speaker == "user")
        .count()
    )
    history_turns = (
        db.query(ConversationTurn)
        .filter(ConversationTurn.session_id == session.id)
        .order_by(ConversationTurn.created_at.asc(), ConversationTurn.id.asc())
        .all()
    )
    conversation_history = [
        {
            "speaker": turn.speaker,
            "text_en": turn.text_en,
            "text_cn": turn.text_cn,
        }
        for turn in history_turns
    ]
    ai_client = get_ai_client()
    generated_turn = await ai_client.continue_conversation(
        _session_to_generated(session),
        user_turns_count,
        payload.text_en.strip(),
        conversation_history,
    )
    system_turn = ConversationTurn(
        session_id=session.id,
        speaker="system",
        text_en=generated_turn.text_en,
        text_cn=generated_turn.text_cn,
        input_mode="system",
    )
    db.add(system_turn)
    db.commit()
    db.refresh(user_turn)
    db.refresh(system_turn)
    refreshed = get_session(db, session.id)
    if refreshed is None:
        raise ValueError("Session not found after turn creation")
    return user_turn, system_turn, _session_response(refreshed)


async def complete_session(db: Session, session: ScenarioSession) -> ConversationEvaluation:
    turns = (
        db.query(ConversationTurn)
        .filter(ConversationTurn.session_id == session.id)
        .order_by(ConversationTurn.created_at.asc())
        .all()
    )
    user_turns = [turn.text_en for turn in turns if turn.speaker == "user"]
    ai_client = get_ai_client()
    evaluation = await ai_client.evaluate_conversation(_session_to_generated(session), user_turns)
    session.status = "completed"
    session.completed_at = datetime.utcnow()
    session.evaluation = evaluation.model_dump()
    db.commit()
    db.refresh(session)
    return evaluation


def get_session(db: Session, session_id: int) -> ScenarioSession | None:
    return (
        db.query(ScenarioSession)
        .options(joinedload(ScenarioSession.turns))
        .filter(ScenarioSession.id == session_id)
        .first()
    )


def list_history(db: Session, limit: int = 20) -> list[ScenarioSessionResponse]:
    sessions = (
        db.query(ScenarioSession)
        .options(joinedload(ScenarioSession.turns))
        .order_by(ScenarioSession.created_at.desc())
        .limit(limit)
        .all()
    )
    return [_session_response(session) for session in sessions]


def create_favorite(db: Session, payload: FavoriteCreateRequest) -> FavoriteExpression:
    favorite = FavoriteExpression(**payload.model_dump())
    db.add(favorite)
    db.commit()
    db.refresh(favorite)
    return favorite


def list_favorites(db: Session) -> list[FavoritesByCategory]:
    favorites = (
        db.query(FavoriteExpression)
        .order_by(FavoriteExpression.category.asc(), FavoriteExpression.created_at.desc())
        .all()
    )
    grouped: dict[str, list[FavoriteResponse]] = {}
    for favorite in favorites:
        grouped.setdefault(favorite.category, []).append(FavoriteResponse.model_validate(favorite))
    return [FavoritesByCategory(category=category, items=items) for category, items in grouped.items()]


def delete_favorite(db: Session, favorite_id: int) -> bool:
    favorite = db.get(FavoriteExpression, favorite_id)
    if favorite is None:
        return False
    db.delete(favorite)
    db.commit()
    return True
