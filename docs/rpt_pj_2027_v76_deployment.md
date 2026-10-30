# RPT PJ 2027 v76 — controlled deployment checklist

Status: STAGING. Do not merge until CI passes and app.py integration is reviewed.

## Inputs
- 48 Word documents from `CikguLaju_RPT_PJ_2027_48_DOCX_v76_KALENDAR_DISAHKAN_STAGING.zip`.
- Filenames follow `RPT_PJ_2027_{state}_Tahun_{year}_v76_STAGING.docx`.
- 16 states, 3 years (4, 5, 6), 48 files.
- Approved 2027 calendar snapshot and `final_audit_evidence.json` already committed.

## Safe installation
1. Provision a persistent, non-symlinked data directory outside existing app assets.
2. Run `python scripts/verify_rpt_pj_2027_v76.py /path/to/v76.zip`.
3. Run the pinned installer: `python scripts/provision_rpt_pj_2027_v76.py /path/to/v76.zip /path/to/NEW_VERSIONED_DATA_DIR`. It verifies SHA-256 and 48 Word files and refuses an existing destination.
4. Run `python scripts/audit_rpt_pj_2027_readiness.py /path/to/NEW_VERSIONED_DATA_DIR`.
5. Verify all 48 files exist in `/path/to/data/RPT_PJ_2027_DOCX/`.
6. Never overwrite existing RPT files; install to a fresh versioned directory when upgrading.

## Telegram integration contract
- Existing access checks MUST supply `is_developer`, `subscription_active`, or `rakan_pembangun_active` from trusted server-side state.
- Free users see RPT menu teaser but cannot download documents.
- Use `can_download_rpt` to compute the boolean, and `deliver_selected_rpt` for authorized delivery.
- Never accept `paid_access` from Telegram callback data.
- Only expose Years 4–6 for Pendidikan Jasmani in this batch.
- Catch `RPTAccessDenied`, `RPTDocumentUnavailable`, and invalid state/year errors in the Telegram handler.
- Validate real Telegram delivery before enabling the menu.
- Keep other RPT subjects and all existing DB tables unchanged.

## Release gates
- CI green.
- 48 Word documents provisioned on the target service.
- Final calendar evidence audit green.
- Manual Telegram access tests: developer, Rakan Pembangun, active subscriber, free user.
- Confirm existing RPH and payment flows unaffected.
- Merge/deploy only after these checks pass.

## Render service identified (read-only check 2026-10-30)
- Workspace: Nuryn Ayreen's workspace, ID `tea-daft3g2d0e5s73dtig1g`.
- Service: `CikguLaju-AI`, ID `srv-dah3b8lbedkc738ugqt0`.
- Repo: `nurynayreen88/CikguLaju-AI`; branch: `main`.
- **Auto-deploy on commit to main is enabled.** Do not merge PR #70 until all release gates pass.
- Build: `bash build_jawi.sh`; start: `gunicorn app:app`.
- Service runtime: Python, Oregon; no persistent disk has been verified.
- Do not assume manually copied files survive redeploy. Establish a repeatable asset delivery mechanism (or a verified persistent disk) before release.
- The approved 48-file ZIP is not committed in PR #70; the CSV snapshot and code alone do not supply downloadable DOCX files.
- Existing `app.py` remains unchanged in PR #70. The opt-in menu and callback bridge are **not live** until registered in the existing bot and supplied a trusted user-ID authorization resolver.

## Current CI limitation
- GitHub Actions run #74 (run ID `41003933343`) concluded failure. Job metadata exposed no steps or logs, so the failure reason is unverified. Do not report tests as passing or merge based on locally checked assets alone.
