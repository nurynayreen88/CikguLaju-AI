# Web V1 — traced generation entrypoints (source-only)

Verified from `app.py` blob `343af186f9ce97a4240e3afe6a0f3bdd1a93f91f` on `main`.

- The PDF builder is `create_pdf_file(s, ai_text, cid)`. It constructs a PDF in the OS temporary directory and depends on the lesson state and rendered RPH text.
- English RPH generation includes `_eng_verified_teacher_rph_text(s)` and `_local_rph_text(s)`; do not call them with a partially populated state.
- `_rph_rows` has late adapters that import `english_y3_standalone_render.apply` and a Year 2 standalone adapter. These must be preserved; web must reuse the final bound implementation rather than bypassing wrappers.
- `_rph_cache_key(s)` includes year, subject, topic, subtopic, SK/SP, textbook book/page/lesson/focus, RPH mode and variation seed. These fields matter to exact lesson identity.
- Credit balance and consumption use Supabase REST/RPC; local SQLite credit tables are not authoritative for runtime credit.
- The existing `_consume_generation_credit` generates a fresh random reference for each call. A web request retry requires a separately audited idempotency strategy before enabling paid generation.

**Not yet verified:** exact final PDF/DOCX routing, English Year 2/3 standalone module presence and content, successful generation credit transaction ordering, final deployed DB files, web session authentication.

**Implementation gate:** do not enable generation from Web V1 until final state assembly, wrapper chain, output path handling, authorization, credit transaction and retries are verified with isolated tests.
