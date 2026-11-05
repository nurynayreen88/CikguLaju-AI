# Matematik Tahun 2–6 — v37 staging release gate (5 November 2026)

**Keputusan:** LULUS TEKNIKAL 585/585. **FINAL READY AKADEMIK = FALSE. TELEGRAM LIVE VERIFIED = FALSE.**

## Perubahan sebenar
- Sambung daripada v36: 117 RPH Word, PDF dan Markdown Tahun 4 diubah **pada medan rujukan sahaja** untuk memindahkan catatan dalaman "SP tercatat … bukan bukti padanan aktiviti buku" ke rekod audit, tanpa mereka-reka halaman latihan. Semua aktiviti, SP, objektif dan PBD dikekalkan.
- Tahun 2, 3, 5 dan 6 **468 Lesson** byte-identical daripada v36 bagi Word/PDF/Markdown masing-masing.
- Pakej v37 mengandungi 585 Word, 585 PDF individu, 585 Markdown dan lima PDF tahunan (117 muka setiap tahun). **585/585 PDF satu halaman A4**, tiada pendua ID/fail, semakan arkib `testzip` lulus.
- SHA-256 ZIP `CIKGULAJU_MATEMATIK_v37_585_RPH_TEACHER_VIEW_STAGING.zip`: `54f66a68e5cdc272c358d1f905657c80b2647f5616fa30a6b1055e02097b95f9`; saiz **48,328,068 bytes**.
- Matriks audit 585 baris `CIKGULAJU_MATEMATIK_V37_585_RPH_RELEASE_MATRIX_20261105.csv`; SHA-256 `c2e83dec5c682335268f21db6e19dfae640e7a7338bc4ee285be36ba3945de6d`. Semua 585 membuktikan **lokasi kod SP di PDF Buku Teks**, bukan pelaksanaan tepat aktiviti buku.
- Modul pratonton **staging sahaja** ada dalam [branch isolated](https://github.com/nurynayreen88/CikguLaju-AI/tree/staging/matematik-v37-rph-preview-20261105). Mempunyai guard environment opt-in, SHA256 fail-closed dan akses berbayar/admin. **9/9 ujian setempat menggunakan pakej sebenar lulus** (semak 585 PDF + kawalan akses); **bukan** penghantaran Telegram sebenar.

## Syarat FINAL READY yang belum disahkan
1. Kandungan aktiviti, pengiraan/PBD dan rujukan halaman sebenar Buku Teks & Buku Aktiviti untuk **585/585** RPH perlu audit akademik individu, bukan cuma semakan kod SP dan format.
2. T4: **117 Lesson dihasilkan daripada 83 ID RPH sumber**; 34 sesi pecahan tambahan perlu disahkan berasaskan RPH asal dan aktiviti buku.
3. Takwim negeri 2027, cuti umum/gantian dan jadual waktu sebenar perlu diuji mengikut negeri/guru.
4. Kod runtime semasa dalam `main` hanya mempunyai muat turun **RPT Matematik v28 DRAF**; **v37 RPH belum dipasang ke DB kanonik, menu Telegram atau Web**. Perlu ujian staging end-to-end terhadap DB sumber sebenar, kuota percubaan/langganan serta regresi subjek lain sebelum deploy.
5. Keadaan `main` berubah serentak oleh kerja subjek lain. Sebelum merge, banding semula diff, backup/version DB serta CI semua integrasi.

**Kawalan:** tiada fail produksi / user DB / Telegram atau Render diubah, tiada PR untuk merge. Kekalkan `final_ready=false` sehingga bukti setiap gate ada.

Rujuk [v35 release audit](./matematik_v35_release_matrix_585_check_20261105.md), [v32 content](./matematik_v32_189_rph_dedup_quality_gate_20261105.md).
