# Bahasa Arab Tahun 2–6 — checkpoint staging (5 November 2026)

## Terkini
- **30 RPH Markdown DRAF**, PdP 001–006 bagi setiap Tahun 2–6.
- **20 unit** (4 per tahun) pada indeks urutan unit; **30 baris** pemetaan PdP awal kepada kod SK/SP dalam CSV berasingan.
- Semua rekod berstatus **DRAF_SEMAK / BELUM READY**, halaman buku teks PdP individu belum disahkan, **0 FINAL READY**.
- Y3 Unit 4 dalam indeks diperbetulkan kepada **الزمان**, berdasarkan RPT 2026 dan tema DSKP.
- RPH ini bahan kerja awal; bukan 30 RPH yang lulus pengesahan guru atau dipasang ke Telegram/Web.
- Cabang staging berasingan; **tiada** ubah `app.py`, SQLite produksi v26.00 atau Supabase pengguna.

## Kod pada enam PdP awal
| PdP | T2 | T3 | T4 | T5 | T6 |
|---|---|---|---|---|---|
| 001 | 1.1.1 | 1.1.1 | 1.1.1 | 1.1.1 | 1.1.1 |
| 002 | 1.1.2 | 1.1.2 | 1.1.2 | 1.1.2 | 1.1.2 |
| 003 | 1.2.1 | 1.2.1 | 1.2.1 | 1.2.1 | 1.2.1 |
| 004 | 2.1.1 | 2.1.1 | 2.1.1 | 2.1.1 | 2.1.1 |
| 005 | 2.2.1 | 2.2.1 | 2.2.1 | 2.2.1 | 2.2.1 |
| 006 | 3.1.1 | 3.1.1 | 3.1.1 | **3.2.1** | 3.1.1 |

Kod berdasarkan DSKP dan RPT 2026 yang dicapai; jadual ini **pemetaan perancangan** sahaja, bukan semakan manual setiap PdP dengan bukti halaman.

## Sumber rujukan
- DSKP T2–T5: PDF Google Drive pada `source_manifest_20261105.json`.
- DSKP T6: RPT 2026 serta teks DSKP KSSR Semakan Tahun 6 di https://anyflip.com/bpvwr/huxb/basic ; perlu banding PDF asal.
- RPT 2026 T2–T6: URL pada `source_manifest_20261105.json`.
- Buku teks T4/T5 memberi **julat halaman unit**, bukan halaman aktiviti tertentu.
- Buku T2 perlu bukti halaman, buku T3 dan T6 imbasan memerlukan semakan imej.

## Belum siap
1. Susunan semua PdP sepanjang tahun dan RPT 2027 (tarikh Kumpulan A/B/cuti).
2. Buktikan setiap rujukan SK/SP/halaman buku, aktiviti dan pencapaian.
3. Jana dan periksa Word/PDF satu halaman A4 serta susun atur Arab RTL.
4. Audit DB aktif dahulu, gabung sumber Telegram–Web, uji integrasi serta kelulusan guru.

## Semakan teknikal
`python scripts/check_bahasa_arab_t2_t6_stage.py` ialah pemeriksa struktur **baca-sahaja** untuk draf dan mesti dijalankan dalam CI. Kejayaan struktur tidak membuktikan kualiti pedagogi atau status READY.
