from datetime import datetime

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.api.routes import router
from app.core.config import settings
from app.db.session import Base, engine, SessionLocal
from app.models.practice import StoredScenario
from app.services.ai_client import get_ai_client


# Common scenarios to pre-seed at startup
DEFAULT_SCENARIOS = [
    # Level 1 - Beginner scenarios
    {"level": 1, "category": "daily", "scenario_name": "Ice Cream Stand"},
    {"level": 1, "category": "daily", "scenario_name": "Toy Store"},
    {"level": 1, "category": "daily", "scenario_name": "Zoo Ticket Gate"},
    # Level 2 - Intermediate scenarios
    {"level": 2, "category": "academic", "scenario_name": "Asking a Teacher About Homework"},
    {"level": 2, "category": "daily", "scenario_name": "Library Help Desk"},
    {"level": 2, "category": "social", "scenario_name": "School Club Signup"},
    # Level 3 - Advanced scenarios
    {"level": 3, "category": "business", "scenario_name": "Client Meeting"},
    {"level": 3, "category": "business", "scenario_name": "AI 行业面试 (Daily Challenge)"},
    {"level": 3, "category": "travel", "scenario_name": "Hotel Front Desk"},
    {"level": 3, "category": "travel", "scenario_name": "Restaurant Reservation"},
]

async def seed_default_scenarios() -> None:
    """Seed default scenarios at startup if they don't exist in DB."""
    db: Session = SessionLocal()
    try:
        ai_client = get_ai_client()
        for scenario_spec in DEFAULT_SCENARIOS:
            # Check if already exists
            existing = db.query(StoredScenario).filter(
                StoredScenario.level == scenario_spec["level"],
                StoredScenario.category == scenario_spec["category"],
                StoredScenario.scenario_name == scenario_spec["scenario_name"],
            ).first()
            if existing is not None:
                continue

            # Generate via LLM and store
            generated = await ai_client.generate_scenario(
                level=scenario_spec["level"],
                category=scenario_spec["category"],
                scenario_name=scenario_spec["scenario_name"],
            )
            stored = StoredScenario(
                level=generated.level,
                category=generated.category,
                scenario_name=generated.scenario_name,
                scenario_context_cn=generated.scenario_context_cn,
                starter_en=generated.starter_en,
                starter_cn=generated.starter_cn,
                phrases=[phrase.model_dump() for phrase in generated.phrases],
                is_default=True,
            )
            db.add(stored)
            print(f"Seeded default scenario: {generated.scenario_name}")
        db.commit()
    except Exception as e:
        print(f"Warning: scenario seeding failed (non-critical): {e}")
        db.rollback()
    finally:
        db.close()


def create_app() -> FastAPI:
    app = FastAPI(title=settings.app_name)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.on_event("startup")
    async def on_startup() -> None:
        Base.metadata.create_all(bind=engine)
        # Seed default scenarios in background (don't block startup)
        await seed_default_scenarios()

    app.include_router(router, prefix="/api")
    return app


app = create_app()
