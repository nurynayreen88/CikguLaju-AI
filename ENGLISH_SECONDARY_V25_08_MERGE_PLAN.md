# CikguLaju v25.08 — English Secondary additive merge

Tujuan fail ini ialah menambah data Bahasa Inggeris Tingkatan 1–5 ke salinan Master DB semasa secara non-destructive.

## Prinsip keselamatan
- CikguLaju_Curriculum_Master_v24_95_CORE.db kekal dan tidak diubah.
- app.py live tidak diubah.
- DB Bahasa Inggeris Secondary bukan pengganti Master DB.
- Output mesti menggunakan nama DB versi baharu.
- Rekod sedia ada hanya diperkaya jika medan kosong; rekod lama tidak dipadam.
- 560 lesson BI Secondary (112 x 5) mesti wujud selepas merge.
- integrity_check mesti PASS sebelum output diterima.

## Input
1. CikguLaju_Curriculum_Master_v24_95_CORE.db
2. CikguLaju_Curriculum_Master_v25_04_ENGLISH_F1_F5_FINAL_OFFLINE_AUDIT.db
3. merge_english_secondary_into_live_master_v25_08.py

## Output cadangan
CikguLaju_Curriculum_Master_v25_08_CORE_PLUS_ENGLISH_SECONDARY.db

Status: migration prepared; live CORE and live app remain untouched.
