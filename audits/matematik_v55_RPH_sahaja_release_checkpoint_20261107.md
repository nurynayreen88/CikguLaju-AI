# Matematik v55 — RPH Tahun 3 set induksi konkrit (7 November 2026)

**STATUS: DRAFT STAGING | QA ZIP sebenar 12/12 PASS | Akademik FINAL READY = NO.**

## Had skop
- **RPH Matematik Tahun 2–6 sahaja. RPT 2027 bukan sebahagian kerja ini.**
- Tiada semakan/janaan/penulisan RPT; tiada perubahan database, Telegram, Web, Render produksi, akaun, kuota atau bayaran.
- Semua fail dan pembetulan disediakan dalam arkib staging boleh dimuat turun dari perbualan; arkib penuh tidak ditolak ke repositori awam.

## Sumber dan perubahan
- Input v54: `CIKGULAJU_MATEMATIK_v54_585_RPH_SET_INDUKSI_T2_KONKRIT_STAGING.zip`, SHA256 `45daf47da308170c0d5563bc5a66d2486d7413c135790f022d481ff13adac411`.
- Output v55: `CIKGULAJU_MATEMATIK_v55_585_RPH_SET_INDUKSI_T3_KONKRIT_STAGING.zip` (**49,241,164 bait**); SHA256 `3913f179aa5690b8c2b550c5cb65c87aac16157f38db9f1001cb9c2fa9784d7e`.
- Sebanyak **98 daripada 117** RPH Tahun 3 masih ada set induksi generik literal `mengaitkannya dengan tajuk`. Semua **98 intro** diganti dengan **98 soalan/demonstrasi konkrit unik** yang berpaut pada **Aktiviti 1 sebenar RPH**.
- Contoh: T3-L001 membaca 7 405 dan nilai tempat sifar; T3-L029 model 1/2 = 2/4; T3-L055 tambah/tolak wang daripada resit; T3-L074 meminjam 1 jam; T3-L115 petunjuk satu ikon piktograf = 2 buku.
- **19/117** intro Tahun 3 yang sudah khusus tidak ditukar. **487/585** RPH di Tahun 2–6 kekal **byte-identical** dengan v54 di DOCX/PDF/Markdown.
- Setiap perubahan hanya menggantikan seksyen **Set induksi (5 minit)**; SK/SP, objektif, Aktiviti 1/2/3, BA, rujukan buku, penutup dan masa kekal. Rekod sebelum/selepas serta Aktiviti 1 sumber ada dalam `audits/matematik_v55_98_set_induksi_T3_RPH_sahaja_20261107.csv`.
- **Tiada claim** bahawa 98 intro ini mendapat signoff rasmi guru atau verifikasi latihan Buku Aktiviti baharu.

## QA pada arkib nyata
- **12/12** ujian `/mnt/data/math_ready_audit/test_v55_actual_archive.py` PASS, termasuk SHA/CRC ZIP, 98 intro unik, pautan ke Aktiviti 1, hanya satu perenggan Word berubah setiap RPH, Markdown hanya satu ayat berubah, **487 RPH unchanged 3 formats**, **585 PDF satu halaman A4**, **5 PDF gabungan 117 halaman setiap satu**, tiada fail RPT, manifest `final_ready=false`, dan teks pembuka pada setiap PDF Tahun 3.
- Semua **98 DOCX** telah dirender menjadi PDF menggunakan LibreOffice; QA otomatis mengesahkan teks di dalam sempadan A4. Contact sheet enam contoh (**T3-L001, L016, L037, L055, L074, L115**) telah diperiksa secara visual, tanpa clipping/overlap.
- ZIP akhir mengandungi 1821 fail unik; tiada CRC failure, tiada nama duplikat. Year3 gabungan baharu bernama `Tahun_3/RPH_Tahun_3_117_Lesson_Gabungan_v55.pdf`; empat gabungan tahun lain kekal sama.
- Fail loader staging berasingan `rph_standalone/matematik/staging_preview_v55.py`, SHA-locked; ujian `tests/test_matematik_ba_v55_intro_RPH_only_20261107.py` dan `tests/test_matematik_ba_v55_preview_20261107.py`.
- Perincian gate SHA dalam `audits/matematik_v55_release_gate_RPH_only_20261107.json`; arkib juga mempunyai `AUDIT/V55_RELEASE_GATE.json`.

## Release masih HOLD
- **0/585 signoff akademik formal** per item Buku Aktiviti/Buku Teks; sumber dan kandungan RPH lain tidak dianggap verified menyeluruh.
- **34 pasangan Tahun 4** masih perlu semak item teks latihan; pengesahan kod SP sahaja tidak mencukupi.
- Ujian **Telegram–Web E2E staging sebenar** pada DB kanonik belum dibuat. Ujian mock/ZIP luar talian tidak mewakili deployment nyata.
- **Tiada merge PR #444, tiada deploy, tiada data pengguna/kuota/akaun dibaca atau diubah.**
