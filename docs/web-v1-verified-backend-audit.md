# Web V1 — verified backend source inspection (2026-11-01)

Source: GitHub `main` `app.py`, blob SHA `343af186f9ce97a4240e3afe6a0f3bdd1a93f91f`.
The normal file-content endpoint returned empty content, but the Git blob endpoint returned the full source. This audit is **source inspection only**, not a live production database check.

## Verified from source
- Flask application: `app = Flask(__name__)`; existing webhook route `/webhook`.
- `sqlite3` is imported and `_db()` uses `sqlite3.connect(DB_PATH, timeout=15)`.
- `DB_PATH` selects the bundled rebuilt SQLite database when present; otherwise `CIKGULAJU_DB_PATH` or a local recovery filename.
- `_db()` also conditionally attaches worksheet-content SQLite data.
- `curriculum_topics`: `id`, `year_label`, `subject`, `topic`, `subtopic`.
- `curriculum_standards`: `id`, `year_label`, `subject`, `topic`, `subtopic`, `sk_code`, `sk_text`, `sp_code`, `sp_text`, `source`, `verified`.
- `textbook_page_lesson_map` includes `year_label`, `subject`, `unit_title`, `lesson_no`, `focus`, `verified`.
- `rph_cache` has `cache_key`, `rph_text`, `created_at`, `hits`.
- `user_credits` has `chat_id`, `credits`, `free_granted`; `credit_ledger` tracks deltas.
- `user_access` has `chat_id`, `status`, `access_until`; `bot_users` has `chat_id` and profile metadata.
- Source contains `_local_rph_text_english` and document-sending functions; actual generation and entitlement call paths still require inspection.

## Important restrictions
1. Do **not** assume `curriculum_topics` is the authoritative standalone lesson store; determine lesson identity and mapping first.
2. Do **not** expose `chat_id` as a web login mechanism. Authenticate the web user and securely link a Telegram identity after verifying ownership.
3. Do **not** copy or independently decrement `user_credits` from the web; reuse audited server-side quota transactions.
4. Do **not** expose the database path, tokens, SQLite file, or any RPH content through a public endpoint.
5. Keep Web V1 generation disabled until actual RPH and document call paths are verified.
6. Source-level SQLite confirmation does not establish the active production file contents, persistence, concurrency, or backup configuration.

Next: trace the actual standalone lesson lookup and PDF/DOCX generation flow, then implement a read-only catalog adapter with exact verified SQL and integration tests.
