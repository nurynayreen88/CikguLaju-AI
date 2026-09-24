# CikguLaju Student Game App — MVP v1

Separate student-facing learning game app. Do not modify or overwrite the existing CikguLaju curriculum database.

## Goal
Mobile-first/PWA learning games for Malaysian primary pupils (Year 1–6).

## MVP flow
1. Home
2. Choose Year 1–6
3. Choose subject: Bahasa Melayu, English, Matematik, Sains
4. Choose topic
5. Choose game
6. Play
7. Results: score, stars, XP, streak
8. Continue / retry / next level

## Game modes
- Quick Quiz
- Match Pairs
- Arrange Answer
- Memory Cards
- Boss Battle

## Gamification
- XP and levels
- 1–3 stars per stage
- coins
- streaks
- unlockable stages
- progress per subject/topic

## Architecture
Keep game engine independent from curriculum/question content. Content should be data-driven so new questions/topics can be added without changing game code.

Suggested stack:
- Mobile-first PWA
- Frontend: HTML/CSS/JavaScript initially (upgradeable to React)
- Backend: Python Flask/FastAPI
- SQLite for MVP
- PostgreSQL/Supabase-ready schema

## Data model
Student, Subject, Topic, Question, GameSession, Answer, Progress, Reward.

## Safety / preservation
- Existing CikguLaju DB is read-only.
- No destructive migrations.
- If curriculum data is reused later, import/copy only required mappings into the student app DB.
- Keep this app deployable independently from the teacher bot.

## First playable milestone
Build a polished demo with Year 1 Matematik and at least 3 playable topics. Include sample question data, responsive touch UI, progress/XP, results screen, retry and next-level navigation.

## Codex implementation order
1. Scaffold app and DB.
2. Build mobile UI/navigation.
3. Implement Quick Quiz engine.
4. Implement Match Pairs and Arrange Answer.
5. Add scoring, XP, stars and progress persistence.
6. Seed Year 1 Matematik demo content.
7. Add tests and README/run instructions.
