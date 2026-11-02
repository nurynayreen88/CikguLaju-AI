# Telegram ↔ Web authoritative-source audit (2026-11-02)

## Observed from GitHub production branch (read-only)
- `main/app.py` is the Telegram production application (approximately 2.86 MB).
- The repository contains **multiple** versioned curriculum SQLite databases and multipart snapshots, including `v26_00_manifest.json`, `CikguLaju_v26_16.db.part01..03`, and `CikguLaju_Curriculum_Master_v25_99_MATH_T1_T6_CANONICAL.part00..02`.
- File existence and version naming **do not establish which database is mounted or loaded by the running Telegram service**.
- Web's `CIKGULAJU_WEB_PREVIEW_DB` is a separate configured path. Local file identity is not evidence of Telegram runtime parity.
- Supabase account and entitlement lookup is already shared in part, but the curriculum and material lookup paths remain independent.

## Render runtime observations (read-only)
- Telegram service `CikguLaju-AI` runs `main`, build `bash build_jawi.sh`, start `gunicorn app:app`, Render region Oregon, autoDeploy enabled.
- Web staging service runs `staging/cikgulaju-web-v1`, start `gunicorn --bind 0.0.0.0:$PORT tools.run_web_v1_preview:app`, Render region Singapore, autoDeploy disabled.
- These are separate Render instances and filesystems. A local SQLite path cannot be assumed to refer to the same file on both services.

## Confirmed production runtime evidence (2026-11-02)
- Production `main/app.py` selects v26.00 through `_cikgulaju_primary_db_v2600()` and validates `PRAGMA integrity_check`, required RPT tables, and Pendidikan Moral record counts before setting `DB_PATH`.
- Production Render app logs repeatedly show `v26.00 PRIMARY DB ACTIVE /opt/render/project/src/CikguLaju_Curriculum_Master_v26_00.db`, including 2026-11-02 04:53 UTC.
- The app also supports specialist resolvers, shards and supplementary databases. v26.00 is the **primary curriculum database**, not proof that every material or audio comes from it.
- Telegram and Web Render run on separate instances; copying v26.00 to Web would create a snapshot, **not** live synchronization. A shared authoritative data service or authenticated read-only API is still needed.

## Required before connecting Web to production curriculum
1. Inspect **read-only** the production Render service's effective database configuration and app startup selection; do not print secrets.
2. Establish the exact canonical source and whether it is updated in place, versioned at deploy, or fetched from a remote store.
3. Confirm Telegram and Web can read the same **authoritative live service**; copying a GitHub SQLite file is not synchronization.
4. Confirm versioned Lesson/Unit/SK/SP identifiers and approval records; prevent joining material files by an ambiguous lesson number.
5. Connect a read-only shared curriculum adapter to the confirmed service; verify parity across representative lessons and all years.
6. Only after tests, integrate Web dropdown and materials against that adapter. No write or destructive migration.
7. Keep standalone RPH generation disabled until approved document rendering, durable retry accounting and actual template parity pass.

## Guardrail
Do not guess the latest source from filename timestamps, do not modify `main`, and do not silently replace the Web catalog with a snapshot.
