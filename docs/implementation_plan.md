# SpeakScene Implementation Plan

## MVP Scope

The first build proves this learning loop:

```text
Start scenario -> study bilingual phrases -> guided conversation -> full-session evaluation -> favorite useful expressions
```

The product should not require learners to translate a fixed Chinese sentence. The scenario and phrase list provide scaffolding, and the chat area provides active practice.

## Milestones

### 1. Scenario Engine

- FastAPI app with SQLite persistence.
- Scenario start endpoint that returns context, starter line, and 8-12 bilingual phrases.
- Conversation turn endpoint that stores user replies and generates the next system turn.
- Completion endpoint that evaluates the whole conversation.

### 2. Practice UI

- Three-column desktop layout:
  - Left: scenario and bilingual phrasebook.
  - Middle: chat transcript and input tools.
  - Right: evaluation, history, and favorites.
- Mobile layout stacks the same panels.
- Browser TTS reads system turns aloud.
- Voice input uses browser speech recognition where supported.
- Handwriting MVP provides a canvas plus text submit field.

### 3. Favorites

- Expressions can be saved from the phrase list.
- Favorites are grouped by scenario category.
- Users can remove saved expressions.

### 4. AI Provider Upgrade

- Replace deterministic mock generation with real LLM scenario packages.
- Add real conversation continuation and evaluation prompts.
- Add backend STT/TTS providers only after browser MVP proves the flow.

### 5. Accounts And Growth

- Email or WeChat login.
- User-owned history and favorites.
- Scenario flashcards from favorites and weak points.
- Points, streaks, badges, and Pro scenario packs.

## Current Implementation Notes

- `POST /api/scenarios/start` creates a session and starter turn.
- `POST /api/sessions/{session_id}/turns` appends a user turn and a generated system turn.
- `POST /api/sessions/{session_id}/complete` stores the evaluation on the session.
- `GET /api/favorites`, `POST /api/favorites`, and `DELETE /api/favorites/{favorite_id}` manage saved expressions.
- Existing old task/attempt/review tables are not part of the new MVP flow.
