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
3. Run `python scripts/install_rpt_pj_2027_assets.py /path/to/v76.zip /path/to/data`.
4. Run `python scripts/audit_rpt_pj_2027_readiness.py /path/to/data`.
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
