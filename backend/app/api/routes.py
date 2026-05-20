from fastapi import APIRouter, Depends, HTTPException, Response
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.practice import ScenarioSession
from app.schemas.practice import (
    ConversationTurnResponse,
    FavoriteCreateRequest,
    FavoriteReviewRequest,
    FavoriteResponse,
    FavoritesByCategory,
    ScenarioSessionResponse,
    ScenarioStartRequest,
    SessionCompleteResponse,
    TextToSpeechRequest,
    TurnCreateRequest,
    TurnCreateResponse,
    UserResponse,
)
from app.services.practice_service import (
    add_user_turn,
    complete_session,
    create_favorite,
    delete_favorite,
    get_session,
    list_favorites,
    list_history,
    start_scenario,
    get_or_create_default_user,
    review_favorite,
    get_daily_scenario,
)
from app.services.tts_service import TextToSpeechError, synthesize_speech

router = APIRouter()


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@router.get("/users/me", response_model=UserResponse)
def get_me(db: Session = Depends(get_db)) -> UserResponse:
    user = get_or_create_default_user(db)
    return UserResponse.model_validate(user)


@router.get("/scenarios/daily")
def daily_scenario() -> dict:
    return get_daily_scenario()


@router.post("/scenarios/start", response_model=ScenarioSessionResponse)
async def create_scenario(payload: ScenarioStartRequest, db: Session = Depends(get_db)) -> ScenarioSession:
    return await start_scenario(db, payload)


@router.get("/sessions/{session_id}", response_model=ScenarioSessionResponse)
def session_detail(session_id: int, db: Session = Depends(get_db)) -> ScenarioSessionResponse:
    session = get_session(db, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Scenario session not found")
    return ScenarioSessionResponse.model_validate(session)


@router.post("/sessions/{session_id}/turns", response_model=TurnCreateResponse)
async def create_turn(
    session_id: int,
    payload: TurnCreateRequest,
    db: Session = Depends(get_db),
) -> TurnCreateResponse:
    session = db.get(ScenarioSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Scenario session not found")
    try:
        user_turn, system_turn, updated_session = await add_user_turn(db, session, payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return TurnCreateResponse(
        user_turn=ConversationTurnResponse.model_validate(user_turn),
        system_turn=ConversationTurnResponse.model_validate(system_turn),
        session=updated_session,
    )


@router.post("/sessions/{session_id}/complete", response_model=SessionCompleteResponse)
async def finish_session(session_id: int, db: Session = Depends(get_db)) -> SessionCompleteResponse:
    session = db.get(ScenarioSession, session_id)
    if session is None:
        raise HTTPException(status_code=404, detail="Scenario session not found")
    evaluation = await complete_session(db, session)
    return SessionCompleteResponse(session_id=session.id, status="completed", evaluation=evaluation)


@router.post("/tts/speech")
async def create_speech(payload: TextToSpeechRequest) -> Response:
    try:
        audio = await synthesize_speech(payload.text)
    except TextToSpeechError as exc:
        raise HTTPException(status_code=503, detail=str(exc)) from exc
    return Response(content=audio, media_type="audio/mpeg")


@router.get("/history", response_model=list[ScenarioSessionResponse])
def history(limit: int = 20, db: Session = Depends(get_db)) -> list[ScenarioSessionResponse]:
    return list_history(db, limit)


@router.get("/favorites", response_model=list[FavoritesByCategory])
def favorites(db: Session = Depends(get_db)) -> list[FavoritesByCategory]:
    return list_favorites(db)


@router.post("/favorites", response_model=FavoriteResponse)
def add_favorite(payload: FavoriteCreateRequest, db: Session = Depends(get_db)) -> FavoriteResponse:
    user = get_or_create_default_user(db)
    payload.user_id = user.id
    return FavoriteResponse.model_validate(create_favorite(db, payload))


@router.post("/favorites/{favorite_id}/review", response_model=FavoriteResponse)
def review_favorite_endpoint(favorite_id: int, payload: FavoriteReviewRequest, db: Session = Depends(get_db)) -> FavoriteResponse:
    favorite = review_favorite(db, favorite_id, payload.quality)
    if not favorite:
        raise HTTPException(status_code=404, detail="Favorite expression not found")
    return FavoriteResponse.model_validate(favorite)


@router.delete("/favorites/{favorite_id}", status_code=204)
def remove_favorite(favorite_id: int, db: Session = Depends(get_db)) -> Response:
    if not delete_favorite(db, favorite_id):
        raise HTTPException(status_code=404, detail="Favorite expression not found")
    return Response(status_code=204)
