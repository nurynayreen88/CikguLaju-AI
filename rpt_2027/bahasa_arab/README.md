# Bahasa Arab Tahun 2–6 — asas RPT 2027 (staging)

**Tarikh semakan:** 5 November 2026  
**Status:** DRAF / BELUM READY / bukan menu LIVE.

## Apa yang benar-benar disediakan
- `unit_sequence_DRAF_20261105.csv`: 20 unit merentas lima tahun, disusun mengikut turutan kandungan BT/RPT 2026.
- `rph_standalone/bahasa_arab/year{2..6}/lesson_001.md`: lima contoh awal PdP mengikut SK 1.1 / SP 1.1.1 daripada padanan RPT 2026.
- `rph_standalone/bahasa_arab/source_manifest_20261105.json`: fail rujukan sumber dan syarat penerbitan.
- `audits/bahasa_arab_stage_20261105.md`: bukti yang telah ditemui, jurang yang masih terbuka dan perlindungan data.

## Belum dilakukan
- Belum membina jadual RPT 2027 rasmi Kumpulan A/B, tarikh negeri, cuti umum atau tarikh PdP mengikut jadual guru.
- Belum memetakan setiap PdP kepada halaman spesifik buku teks, kod SK/SP rasmi dan pentaksiran yang diluluskan.
- Belum menyediakan RPH penuh, Word/PDF satu halaman A4, ujian pemaparan Arab RTL dan integrasi Telegram–Web.
- Belum menyemak isi DB produksi v26.00; kemungkinan rekod Bahasa Arab sedia ada mesti diaudit sebelum sebarang insert.

**Prinsip:** Tiada deduplikasi/penggantian secara diam-diam, tiada ID PdP berasaskan minggu, tiada status READY sebelum audit manual setiap RPH, tiada perubahan `app.py` atau database melalui PR ini.

## Arahan menyambung dengan selamat
Mulakan dengan membaca sumber dalam manifest, kemudian sahkan setiap tajuk unit di buku teks asal. Bina peta Unit → PdP → SK/SP → muka surat buku teks → aktiviti/PBD. Hanya selepas padanan lulus jana RPH individu dan dokumen RPT 2027 mengikut kalendar Kumpulan A/B serta uji format Word/PDF. Ambil backup serta audit DB dan pengguna sebelum integrasi ke runtime bersama Telegram–Web. Simpan semua draf dalam staging sehingga kelulusan manual.

Jangan gunakan fail CSV ini sebagai jadual waktu atau bahan siap untuk pelanggan; ia hanya indeks urutan unit.
