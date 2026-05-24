# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

SpeakScene is an AI-powered English conversation practice app for Chinese learners. It features a three-column workspace: phrase scaffolding (left), AI conversation practice (center), and intelligent review with scoring (right).

## Backend Commands

```bash
cd backend
source .venv/bin/activate
uvicorn app.main:app --reload
```

Or use the convenience script:
```bash
./backend/start_app.sh
```

API available at `http://localhost:8000`. SQLite database (`speakscene.db`) is created automatically on startup.

## Frontend Commands

```bash
cd frontend
npm install
npm run dev
```

App available at `http://localhost:5173`.

## Configuration

Backend reads from `backend/.env`:
- `AI_PROVIDER=openai` — switch from mock to OpenAI
- `OPENAI_API_KEY`, `OPENAI_MODEL` — OpenAI credentials
- `ELEVENLABS_API_KEY` — optional TTS upgrade

Frontend reads from `frontend/.env` (VITE_API_URL for backend URL if needed).

## Architecture

### Backend (FastAPI + SQLAlchemy)

- `app/main.py` — FastAPI app factory with CORS and startup event
- `app/api/routes.py` — All HTTP endpoints (health, scenarios, sessions, turns, favorites, tts)
- `app/models/practice.py` — SQLAlchemy models: User, ScenarioSession, ConversationTurn, FavoriteExpression
- `app/services/practice_service.py` — Business logic for scenario generation, conversation continuation, session completion, SRS review
- `app/services/ai_client.py` — AI provider abstraction with mock fallback; handles scenario generation, conversation continuation, and evaluation
- `app/services/tts_service.py` — ElevenLabs TTS synthesis (falls back gracefully)
- `app/core/config.py` — Pydantic settings from environment
- `app/db/session.py` — SQLAlchemy engine and session management

### Frontend (React + Vite + Tailwind)

- `frontend/src/App.jsx` — Single-page app with three-column layout; manages all state and API calls
- `frontend/src/api/client.js` — API client functions for all backend endpoints
- Browser TTS uses `speechSynthesis`; voice input uses `SpeechRecognition`/`webkitSpeechRecognition`

### Data Flow

1. `POST /api/scenarios/start` — generates scenario with phrases and starter turn via AI client
2. `POST /api/sessions/{id}/turns` — appends user turn, calls AI to continue conversation
3. `POST /api/sessions/{id}/complete` — evaluates full conversation, updates streak
4. Favorites support SRS (SuperMemo-2) scheduling via `review_favorite()`

### Key Design Decisions

- Mock AI client is the default — dev works without paid keys; falls back on provider failures
- Browser-native speech (Web Speech API) is used for STT/TTS in MVP; backend TTS endpoint exists for ElevenLabs upgrade
- SRS intervals use SM-2 algorithm in `review_favorite()`
- Active Recall: due favorites are injected into scenario context when starting a new session