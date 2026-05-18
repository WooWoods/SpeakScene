# SpeakScene Implementation Plan

## MVP Scope

The first build should prove the learning loop:

```text
Generate task -> learner answers -> AI evaluates -> learner improves
```

Voice, login, social, payments, and WeChat integration should follow only after the text-based loop feels useful.

## Milestones

### 1. Core Engine

- FastAPI app with SQLite persistence.
- Task generation endpoint.
- Answer submission endpoint.
- Hint endpoint.
- Strict feedback schema for score, correction, mistakes, and expression variants.

### 2. Practice UI

- Mobile-first React interface.
- Level and category controls.
- Chinese task card and keyword cards.
- English answer input.
- Feedback panel with multi-dimensional scores.

### 3. Review

- History list.
- Mark mastered / needs review.
- Simple spaced-review queue.

Current implementation:

- `GET /api/review/due` returns unmastered attempts whose review time has arrived.
- `POST /api/review/{attempt_id}/mastered` marks an attempt as mastered.
- Scores below 90 are scheduled for next-day review.
- Scores 90 and above are treated as mastered.

### 4. Accounts

- Email login.
- JWT auth.
- Numeric UID assignment.
- User progress page.

### 5. Voice

- Browser recording through MediaRecorder.
- Speech-to-text endpoint.
- Optional TTS for corrected sentences and flashcards.

### 6. Growth

- Points, streaks, badges, leaderboard.
- Friend search by UID.
- Shareable practice card.
- Free/Pro limits.
