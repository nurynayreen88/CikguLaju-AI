# PM + PJPK v26.16 staging

This branch is staging only. No deployment or production database replacement.

Local package: `CikguLaju_PM_PJPK_STAGING_v26_16.zip` (not yet uploaded to this repository).
Contains: `CikguLaju_Curriculum_Master_v26_16_PJPK_SAFE_RELEASE.db` and `README_STAGING.txt`.

Expected existing records: Pendidikan Moral 252; Pendidikan Jasmani 101; Pendidikan Kesihatan 60. Only 33 PJ Tahun 1 records currently pass the conservative ready-view checks. All other records are partial/unverified and must not be presented as fully mapped.

Next step: transfer binary DB to GitHub under a NEW versioned path, verify checksum and integrity, then adjust runtime DB selection explicitly. Do not overwrite the old DB. Do not deploy without explicit approval.
