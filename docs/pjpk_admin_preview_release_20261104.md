# PJPK admin-only Telegram preview — isolated release branch

This branch was created from the live main commit `47431db35c05a9ed0ec5bee0cf50ffc080d0e843`. It imports
the 400 marked **DRAFT** standalone sources in their own new directory, the
400-record fail-closed manifest, and an admin-only, environment-flag-controlled
read-only Telegram RPH preview bridge. It does **not** merge draft PR #169.

The preview displays 338 numbered PJ/PK RPH for Years 2–6 after excluding
four aquatic supplements, the conflicted PJ Year 6 PdP 033, all old editorial
PK snippets, and unverified KP2027 Year 1.

To opt in, configure `CIKGULAJU_PJPK_PREVIEW_ENABLED=1` in **the appropriate
test environment first**. Only the existing `_is_admin(cid)` authority can
see or select preview records. Existing non-admin flows do not change.

Seven isolated source/selection/security regression tests run in CI. There is
no evidence of live Telegram E2E Word/PDF delivery or teacher content approval.
All 400 source files remain `DRAFT_NOT_APPROVED` and `production_ready=false`.

To ship general READY content, separately pass source, textbook, classroom,
A4, identity/schedule, and real Telegram delivery QA. Do not change the
existing SQLite/Supabase user database or reset RPH credits.
