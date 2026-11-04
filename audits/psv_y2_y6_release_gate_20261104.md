# Gerbang kelulusan PSV Tahun 2–6 — audit susulan 4 November 2026

**Keputusan:** **LULUS AUDIT KONSISTENSI FAIL, BELUM FINAL READY / LIVE.**
**Skop:** PR #196, branch `psv-y2-y6-rpt-rph-2027-staging-20261104`; tiada merge, perubahan database, app produksi atau Telegram.

## Bukti yang telah disemak

| Kriteria | Hasil | Maksud terhad |
|---|---|---|
| RPH PSV T2–T6 | **210/210** (42/tahun) | Fail dibaca semula daripada GitHub dan dipadankan nombor PdP, tajuk, SK/SP, pautan RPH, tempoh 60 minit, struktur pengajaran, rujukan BT/DSKP |
| RPT CSV T2–T6 | **5 fail; 210 baris** | Semua 42 rekod/tahun dan path RPH wujud serta nombor tidak lompat |
| Urutan unit | **50/50** sepadan crosswalk RPT 2026 tersimpan | Tanda baca/huruf besar diabaikan; **bukan** pengesahan makna semua standard |
| RPT Tahun 4 | **10 entri objektif/PBD** dibetulkan | Diambil daripada RPH PdP 001, 005, 009, 013, 017, 022, 026, 030, 034, 038; backup sumber disimpan |
| RPT Tahun 5 | **42 entri objektif/PBD** telah diselaraskan dalam batch terdahulu | Digunakan sebagai asas semakan susulan |
| Tahun 6 Unit 1–3 | **PdP 002–009** | Dibetulkan ikut halaman BT 10–25; bukti pada RPH + RPT CSV + HTML |
| Tahun 6 Unit 6–7 | **PdP 019, 020, 022, 023** | RPH amali dibezakan; Unit 6 resis lemon dan Unit 7 **Sarung Botol Idamanku**, rujukan BT 52–61 |
| Tahun 6 projek | **PdP 026, 042** | SP `5.1.5` untuk mengemas selepas pameran, bukan `5.1.4` (semasa pameran) |
| Minggu 2027 | **42 julat minggu A/B cadangan** | Mengelak blok cuti penggal dan minggu cuti perayaan penuh; *bukan* tarikh kelas sebenar |
| Ujian regresi | **Fail ujian ditambah dan dikemas kini** | Assert turutan unit, sumber semantik terpilih, status DRAF, konsistensi RPT–RPH, julat minggu; **belum ada bukti CI Python lulus** |

**Semakan terarah baharu:** bacaan semula CSV Year4 dan Year6, RPH yang dibetulkan, RPT HTML serta 42 julat minggu melalui connector GitHub; tiada kegagalan dalam skop perbandingan ini. Pembacaan 210 RPH dijalankan dalam 15 kelompok 14. Kod SP bercetak di bawah SK `5.1` untuk T2/T3 dikekalkan sebagai sumber yang diterbitkan tanpa mencipta kod baharu.

## Rujukan kawalan sedia ada

- **Induk projek**: `CikguLaju - RPT 2027 Induk Semua Subjek - Kalendar A dan B - Draf Terkawal`, https://docs.google.com/document/d/1MO37hjLMT5Afzlnq2--rf3jJQKX9BlTdyejZvU6Yau4/edit
- **Matriks cuti projek**: `CIKGULAJU_RPT_2027_KALENDAR_CUTI_FINAL_VERIFIED`, https://docs.google.com/spreadsheets/d/1tf6-B6hmA4U6E0fCROcKpxh-B5uLUQOYBt6TZft_7_k/edit
- **Kalendar akademik KPM 2027**: https://www.moe.gov.my/index.php/kalendar-akademik-semasa
- **DSKP/buku teks**: `rpt_2027/psv/textbook_dskp_source_map_20261104.json`, bersama crosswalk sumber tahun 2026.

Dokumen induk menghendaki **RPT Word lanskap berasingan Kumpulan A/B dengan muka depan**, tempoh, tarikh berdasarkan negeri, PBD dan status sumber. Matriks cuti sendiri menunjukkan beberapa cuti gantian negeri **belum sah**; oleh itu minggu yang dihasilkan hanya jadual rujukan CADANGAN dan kolum `Tarikh A`/`Tarikh B` kekal kosong dalam semua lima CSV RPT. Jangan isi atau memaparkan tarikh kelas muktamad berdasarkan julat minggu ini.

## Gerbang masih terbuka: jangan merge / jangan label READY

1. **Makna SK/SP**: pengesahan aktiviti berbanding teks lengkap setiap SP DSKP, 210 PdP satu demi satu; semakan kewujudan kod tidak memadai.
2. **Buku teks**: audit visual semua halaman sumber Tahun 2–6 (terutama 3D, projek, alat, keselamatan dan halaman sebenar) belum diluluskan semuanya; pembetulan khusus masih mendedahkan isu semantik yang terlepas audit struktur.
3. **Jadual**: slot mata pelajaran 2027 pada kelas/negeri, cuti perayaan/gantian/tempatan Kumpulan A/B, peruntukan waktu dan pameran penggal belum disahkan; jangan guna julat minggu cadangan sebagai tarikh tepat.
4. **Hasil dokumen**: 10 RPT Word (.docx) lanskap A/B dengan muka depan dan PDF belum dijana/semak visual. Semua 210 RPH Word/PDF A4 satu halaman juga belum dikeluarkan dan diperiksa cetak.
5. **Ujian kod & CI**: Python `unittest`, semua CI GitHub serta ujian sebenar enjin Word/PDF belum dilaporkan lulus. Bacaan connector bukan pengganti.
6. **Integrasi**: 499 fail PR dilihat; hanya folder `audits`, `rph_standalone`, `rpt_2027`, `tests`. **Tiada perubahan kod app/bot dalam PR**. Tidak ada bukti fail PSV sudah dipilih/dijana dengan betul oleh Telegram/staging atau database.
7. **Kebenaran keluaran**: dokumen induk menyatakan semakan akhir/kelulusan sebelum status READY/pengaktifan; jangan dedahkan label audit dalaman kepada pengguna umum.

## Penyimpanan & sifat tidak merosakkan

- Backup lama projek serta backup RPT Tahun 4 `rpt_2027/psv/backups/RPT_PSV_Tahun_4_2027_DRAF_before_objectives_20261104.csv` dipelihara.
- Pembetulan semasa hanya pada branch staging PR #196; `main`, Telegram LIVE, Supabase dan database sedia ada tidak disentuh.
- Semakan regresi: `tests/test_psv_rpt_rph_alignment.py` dan `tests/test_psv_rpt_rph_source_order.py`.
- Penjadualan kelompok: `rpt_2027/psv/PSV_2027_minggu_PdP_kumpulan_A_B_CADANGAN.csv`.

**Kesimpulan:** kelengkapan dan konsistensi dokumen **lulus**, pengesahan sistem end-to-end dan ketepatan PdP penuh **belum lulus**. Semua status kekal `DRAF_SEMAK` sehingga bukti gerbang lengkap, bukannya menukar status demi sasaran peratus.
