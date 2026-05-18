# SpeakScene

SpeakScene is an AI-powered scenario English practice app for Chinese learners. The MVP focuses on a scenario-led conversation loop:

1. Choose a scenario category and level.
2. Review common bilingual phrases for that scenario.
3. Let the system start the conversation and read the starter aloud.
4. Reply by voice, typing, or handwriting-pad text submit.
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

- The backend currently uses a local mock AI service by default so development can continue without paid API keys.
- Browser TTS uses `speechSynthesis`; voice input uses `SpeechRecognition` or `webkitSpeechRecognition` where available.
- Handwriting input is a canvas plus manual text submit in this MVP; OCR is future work.
- SQLite creates the new scenario/session/favorites tables automatically during backend startup.
