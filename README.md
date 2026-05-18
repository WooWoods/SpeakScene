# SpeakScene

SpeakScene is an AI-powered scenario English practice app for Chinese learners. The MVP focuses on the core loop:

1. Generate a level-specific Chinese scenario.
2. Show core English keyword cards.
3. Let the learner answer in English.
4. Return structured AI feedback with score, corrections, and better alternatives.

## Project Layout

```text
backend/   FastAPI, SQLite, SQLAlchemy, prompt and practice services
frontend/  React, Vite, Tailwind CSS practice interface
docs/      Implementation notes
```

## Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload
```

The API will be available at `http://localhost:8000`.

MVP endpoints:

- `POST /api/tasks/generate`
- `POST /api/attempts/submit`
- `POST /api/hints`
- `GET /api/history`
- `GET /api/review/due`
- `POST /api/review/{attempt_id}/mastered`

## Frontend

```powershell
cd frontend
npm install
npm run dev
```

The app will be available at the URL printed by Vite, usually `http://localhost:5173`.

## MVP Notes

- The backend currently uses a local mock AI service by default so development can continue without paid API keys.
- Add real LLM/STT/TTS providers behind `backend/app/services/ai_client.py`.
- SQLite is created automatically at `backend/speakscene.db` during backend startup.
- Review logic is intentionally simple: low-score attempts return the next day, mastered attempts are delayed for 30 days.
