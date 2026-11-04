# RPT 2027 — Audit Kandungan dan Gerbang Penerbitan

Tarikh audit: 2026-10-27
Repositori: nurynayreen88/CikguLaju-AI
Asas menu: PR #23, feat/rpt-2027-subject-group-navigation-20261025

## Penemuan yang telah disahkan daripada patch PR #23
- Menu Tahun 1–6 dan Tingkatan 1–5 wujud.
- Pilihan sembilan subjek dan Kumpulan A/B wujud.
- Semua kombinasi masih memaparkan 'Dalam pembangunan / semakan'.
- Tiada pemetaan fail RPT yang telah disahkan dalam patch ini.
- Senarai subjek adalah sama untuk semua peringkat; kesesuaian kurikulum perlu disemak.

## Skema rekod RPT 2027 yang perlu disahkan
Setiap rekod: tahun/tingkatan, subjek, kumpulan takwim, urutan PdP (bukan minggu sebagai ID), unit/tajuk, SK, SP, aktiviti ringkas, sumber buku teks/DSKP/RPT/SOW, halaman sumber jika ada, tempoh PdP, status semakan dan versi sumber.

## Gerbang status
DRAFT: bahan belum lengkap atau belum dipadankan.
SOURCE_REVIEW: sumber DSKP/RPT/SOW/buku teks perlu disahkan.
CONTENT_REVIEW: urutan PdP, SK/SP, agihan masa perlu diaudit.
READY: sumber tepat dan kandungan diluluskan, fail output diuji.
BLOCKED: sumber bercanggah, hilang, atau tidak relevan dengan tahun/subjek.

Jangan paparkan fail DRAFT/SOURCE_REVIEW/CONTENT_REVIEW/BLOCKED sebagai sedia dimuat turun.

## Urutan kerja
1. Inventori fail RPT/SOW/DSKP dan buku teks sedia ada bagi setiap tahun dan subjek.
2. Semak kesesuaian subjek mengikut tahun/tingkatan sebelum membina menu bersyarat.
3. Sahkan takwim rasmi KPM 2027 Kumpulan A/B dan negeri, cuti, serta hari persekolahan; jangan mereka tarikh.
4. Padankan urutan PdP dengan SK/SP dan buku teks; gunakan Lesson/PdP sebagai identiti.
5. Semak setiap output Word/PDF dan kaitan dengan RPH Hari Ini.
6. Uji semua status, butang kembali dan fallback; kekalkan DB produksi.

## Keselamatan perubahan
- Tiada reset, overwrite atau migrasi DB produksi.
- Sebarang perubahan app.py perlu py_compile dan ujian callback.
- Sebarang DB calon perlu backup, PRAGMA integrity_check, audit FK/orphan/duplicate.
- Jangan merge atau deploy sebelum kelulusan dan QA.
