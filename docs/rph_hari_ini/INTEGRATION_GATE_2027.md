# RPH Hari Ini — Integration Gate (27 October 2026)

Status: **STAGING / NOT DEPLOYABLE**. This is an audit contract, not a completed bot integration.

## Confirmed architecture
- School state from the teacher's existing profile selects the applicable KPM group, weekends and verified national/state holidays.
- Timetable sessions select class, subject and scheduled date/time. Consecutive timetable slots with the same verified session ID may be grouped; do not infer two lessons merely from two timetable slots.
- RPT/SOW provides the ordered lesson sequence. Each (teacher, class, subject, school year) has independent confirmed progress. **School year must be included in the production progress key** to prevent cross-year leakage.
- Daily suggestions and weekly previews are read-only. The next lesson is derived from fresh progress; it does not advance by date.
- Confirmation requires a valid eligible session, unique confirmation event, transaction lock, re-read of current progress, compare-and-swap update and rollback on failure.
- Missing or unverified calendar records must fail closed. Never treat provisional 2027 holidays as official.

## Existing staging code reviewed
Local isolated reference modules: `completion_guard_v14.py`, `sqlite_completion_v15.py`, `db_readiness_v17.py`.
The v15 test schema uses `(teacher_id,class_id,subject_id)` as the progress key and **does not include school year**; it must not be transplanted unchanged to production. It creates namespaced test tables and is not wired to CikguLaju's existing database.

## Mandatory preflight before modifying the bot
1. Read the real `app.py`, DB configuration, existing teacher profile, timetable and progress schema. GitHub connector currently returns empty `app.py` content; do not guess field names.
2. Take a versioned backup of the actual SQLite database. Run `PRAGMA integrity_check` and `PRAGMA foreign_key_check` on the **copy**, plus SHA-256 before/after read-only inspection.
3. Explicitly map existing IDs and school year, state codes, timetable session identity, and completion semantics. No destructive migrations or overwrites.
4. Verify KPM 2027 school terms and applicable official federal/state public holidays before enabling calendar-driven suggestions.
5. Integration tests: two states with different holidays; same state with different timetables; two classes; two subjects; double period vs separate sessions; duplicate confirmation; stale preview; year rollover; rollback on failure; class-specific progress.
6. Stage only; require review and green tests before any merge or deployment.

## Current blockers
- Production SQLite copy and actual application schema not yet audited.
- Official 2027 state-holiday mapping incomplete.
- No production integration or live RPH Hari Ini test performed.

**Never claim this document makes RPH Hari Ini live.**
