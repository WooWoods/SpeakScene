from datetime import date, datetime

from sqlalchemy import Date, DateTime, Float, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    uid: Mapped[str] = mapped_column(String(16), unique=True, index=True)
    nickname: Mapped[str] = mapped_column(String(80), default="Guest Learner")
    level: Mapped[int] = mapped_column(Integer, default=3)
    points: Mapped[int] = mapped_column(Integer, default=0)
    last_practice_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    streak_days: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    sessions: Mapped[list["ScenarioSession"]] = relationship(back_populates="user")


class ScenarioSession(Base):
    __tablename__ = "scenario_sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    level: Mapped[int] = mapped_column(Integer, index=True)
    category: Mapped[str] = mapped_column(String(80), index=True)
    scenario_name: Mapped[str] = mapped_column(String(160))
    scenario_context_cn: Mapped[str] = mapped_column(Text)
    starter_en: Mapped[str] = mapped_column(Text)
    starter_cn: Mapped[str] = mapped_column(Text)
    phrases: Mapped[list[dict]] = mapped_column(JSON, default=list)
    status: Mapped[str] = mapped_column(String(24), default="active", index=True)
    evaluation: Mapped[dict | None] = mapped_column(JSON, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)

    user: Mapped[User | None] = relationship(back_populates="sessions")
    turns: Mapped[list["ConversationTurn"]] = relationship(
        back_populates="session",
        cascade="all, delete-orphan",
        order_by="ConversationTurn.created_at",
    )


class ConversationTurn(Base):
    __tablename__ = "conversation_turns"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    session_id: Mapped[int] = mapped_column(ForeignKey("scenario_sessions.id"), index=True)
    speaker: Mapped[str] = mapped_column(String(16), index=True)
    text_en: Mapped[str] = mapped_column(Text)
    text_cn: Mapped[str | None] = mapped_column(Text, nullable=True)
    input_mode: Mapped[str] = mapped_column(String(24), default="typing")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    session: Mapped[ScenarioSession] = relationship(back_populates="turns")


class FavoriteExpression(Base):
    __tablename__ = "favorite_expressions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    category: Mapped[str] = mapped_column(String(80), index=True)
    scenario_name: Mapped[str] = mapped_column(String(160), index=True)
    phrase_en: Mapped[str] = mapped_column(Text)
    phrase_cn: Mapped[str] = mapped_column(Text)
    usage_note_cn: Mapped[str] = mapped_column(Text, default="")

    # SRS Fields (SuperMemo-2)
    next_review_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    repetition: Mapped[int] = mapped_column(Integer, default=0)
    interval: Mapped[int] = mapped_column(Integer, default=1)
    ease_factor: Mapped[float] = mapped_column(Float, default=2.5)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class StoredScenario(Base):
    """Cached generated scenarios keyed by (level, category, scenario_name).

    Phrases are stored once and reused on subsequent page loads rather than
    calling the LLM every time.
    """
    __tablename__ = "stored_scenarios"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    level: Mapped[int] = mapped_column(Integer, index=True)
    category: Mapped[str] = mapped_column(String(80), index=True)
    scenario_name: Mapped[str] = mapped_column(String(160), index=True)
    scenario_context_cn: Mapped[str] = mapped_column(Text)
    starter_en: Mapped[str] = mapped_column(Text)
    starter_cn: Mapped[str] = mapped_column(Text)
    phrases: Mapped[list[dict]] = mapped_column(JSON, default=list)
    is_default: Mapped[bool] = mapped_column(default=False)  # True for pre-seeded scenarios
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    