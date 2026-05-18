from datetime import datetime, timedelta

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, JSON, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.session import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    uid: Mapped[str] = mapped_column(String(16), unique=True, index=True)
    nickname: Mapped[str] = mapped_column(String(80), default="Guest Learner")
    level: Mapped[int] = mapped_column(Integer, default=3)
    points: Mapped[int] = mapped_column(Integer, default=0)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    tasks: Mapped[list["PracticeTask"]] = relationship(back_populates="user")


class PracticeTask(Base):
    __tablename__ = "practice_tasks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    user_id: Mapped[int | None] = mapped_column(ForeignKey("users.id"), nullable=True)
    level: Mapped[int] = mapped_column(Integer, index=True)
    category: Mapped[str] = mapped_column(String(80), index=True)
    task_name: Mapped[str] = mapped_column(String(120))
    cn_sentence: Mapped[str] = mapped_column(Text)
    context_cn: Mapped[str] = mapped_column(Text)
    keywords: Mapped[list[dict]] = mapped_column(JSON, default=list)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    user: Mapped[User | None] = relationship(back_populates="tasks")
    attempts: Mapped[list["PracticeAttempt"]] = relationship(back_populates="task")


class PracticeAttempt(Base):
    __tablename__ = "practice_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    task_id: Mapped[int] = mapped_column(ForeignKey("practice_tasks.id"), index=True)
    user_input: Mapped[str] = mapped_column(Text)
    feedback: Mapped[dict] = mapped_column(JSON)
    score: Mapped[int] = mapped_column(Integer, index=True)
    mastered: Mapped[bool] = mapped_column(Boolean, default=False)
    review_due_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=lambda: datetime.utcnow() + timedelta(days=1),
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    task: Mapped[PracticeTask] = relationship(back_populates="attempts")
