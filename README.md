# SpeakScene

SpeakScene is an AI-powered scenario English practice app for Chinese learners. The MVP focuses on a scenario-led conversation loop:

1. Choose a scenario category and level.
2. Review common bilingual phrases for that scenario.
3. Let the system start the conversation and read the starter aloud.
4. Reply by voice or typing.
5. Complete the conversation and receive multidimensional feedback.
6. Favorite authentic expressions by scenario category.

## Project Layout

```text
backend/   FastAPI, SQLite, SQLAlchemy, scenario conversation services
frontend/  React, Vite, Tailwind CSS three-column practice workspace
docs/      Implementation notes
```

## Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

Or run:

```bash
./backend/start_app.sh
```

The API will be available at `http://localhost:8000`.

The backend defaults to the local mock AI provider in code so development works without paid keys. To use real OpenAI scenario generation, conversation continuation, and evaluation, set:

```bash
AI_PROVIDER=openai
OPENAI_API_KEY=your_api_key
OPENAI_MODEL=gpt-5.4-mini
```

If the OpenAI key is missing or a provider call fails, the backend falls back to the mock AI client so the practice flow remains usable.

MVP endpoints:

- `POST /api/scenarios/start`
- `GET /api/sessions/{session_id}`
- `POST /api/sessions/{session_id}/turns`
- `POST /api/sessions/{session_id}/complete`
- `GET /api/history`
- `GET /api/favorites`
- `POST /api/favorites`
- `DELETE /api/favorites/{favorite_id}`

## Frontend

```bash
cd frontend
npm install
npm run dev
```

The app will be available at the URL printed by Vite, usually `http://localhost:5173`.

## MVP Notes

- The backend can use OpenAI for real LLM scenario generation, conversation continuation, and evaluation; mock AI remains the fallback for local development and provider failures.
- Browser TTS uses `speechSynthesis`; voice input uses `SpeechRecognition` or `webkitSpeechRecognition` where available.
- SQLite creates the new scenario/session/favorites tables automatically during backend startup.
