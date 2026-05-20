from datetime import datetime, timedelta, date

from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func

from app.models.practice import ConversationTurn, FavoriteExpression, ScenarioSession, User
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

def get_or_create_default_user(db: Session) -> User:
    user = db.query(User).first()
    if not user:
        user = User(uid="default", nickname="Guest Learner")
        db.add(user)
        db.commit()
        db.refresh(user)
    return user

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
    user = get_or_create_default_user(db)
    if not payload.user_id:
        payload.user_id = user.id
        
    # Active Recall: fetch due favorites
    due_favorites = db.query(FavoriteExpression).filter(
        FavoriteExpression.user_id == user.id,
        FavoriteExpression.next_review_date <= datetime.utcnow()
    ).limit(2).all()
    
    recall_prompt = ""
    if due_favorites:
        phrases = [f.phrase_en for f in due_favorites]
        recall_prompt = f" ACTIVE RECALL: Please subtly prompt the user to use these phrases during the conversation: {', '.join(phrases)}."

    ai_client = get_ai_client()
    generated = await ai_client.generate_scenario(payload.level, payload.category, payload.scenario_name)
    
    if recall_prompt:
        generated.scenario_context_cn += f"\n\n(AI 记忆提示：在对话中试着使用你之前收藏的短语吧！)"
        
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
    
    # Streak Logic
    user = get_or_create_default_user(db)
    today = date.today()
    if user.last_practice_date != today:
        if user.last_practice_date == today - timedelta(days=1):
            user.streak_days += 1
        else:
            user.streak_days = 1
        user.last_practice_date = today
        
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


def review_favorite(db: Session, favorite_id: int, quality: int) -> FavoriteExpression | None:
    favorite = db.get(FavoriteExpression, favorite_id)
    if not favorite:
        return None
        
    # SM-2 Algorithm
    if quality >= 3:
        if favorite.repetition == 0:
            favorite.interval = 1
        elif favorite.repetition == 1:
            favorite.interval = 6
        else:
            favorite.interval = int(round(favorite.interval * favorite.ease_factor))
        favorite.repetition += 1
    else:
        favorite.repetition = 0
        favorite.interval = 1
        
    favorite.ease_factor = favorite.ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    if favorite.ease_factor < 1.3:
        favorite.ease_factor = 1.3
        
    favorite.next_review_date = datetime.utcnow() + timedelta(days=favorite.interval)
    db.commit()
    db.refresh(favorite)
    return favorite


def get_daily_scenario() -> dict:
    return {
        "level": 3,
        "category": "business",
        "scenario_name": "AI 行业面试 (Daily Challenge)",
        "description": "这是今天的每日挑战，完成可获得双倍奖励哦！"
    }
