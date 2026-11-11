# Matematik v56 — 176 set induksi Tahun 5–6, RPH sahaja

**Tarikh:** 7 November 2026. **STATUS: STAGING DRAFT; QA ARKIB SEBENAR 12/12 PASS; BELUM FINAL READY AKADEMIK.**

## Arahan skop yang dipatuhi
- **RPH Matematik Tahun 2–6 sahaja.** RPT 2027 diurus dalam chat lain, jadi **tidak dibaca, diaudit, dibina atau ditulis** dalam sesi ini.
- Tidak menyentuh DB, Render produk, sistem login, kuota RPH, langganan, akaun atau proses pembayaran.

## Output v56
- **Sumber:** `CIKGULAJU_MATEMATIK_v55_585_RPH_SET_INDUKSI_T3_KONKRIT_STAGING.zip`, SHA256 `3913f179aa5690b8c2b550c5cb65c87aac16157f38db9f1001cb9c2fa9784d7e`.
- **Hasil:** `CIKGULAJU_MATEMATIK_v56_585_RPH_SET_INDUKSI_T5_T6_KONKRIT_STAGING.zip`, **48,930,951 bait**, SHA256 `f6c50114698826060bac92355ca1e476e9bf6ca921785cd0b2138e935b773695`.
- **70 daripada 117** RPH Tahun 5 dan **106 daripada 117** RPH Tahun 6 menggunakan frasa set induksi generik `mengaitkannya dengan tajuk`. Kesemua **176** diganti dengan **176 set induksi berbeza**, berupa pertanyaan atau demonstrasi konkrit **berasaskan Aktiviti 1 RPH sedia ada**.
- Contoh T5-L005: 241 494 pada garis 200 000–300 000 untuk pilih ratus ribu terdekat; T5-L035: model 1 1/2 kepada 150%; T5-L053: tunai RM1 200 atau kredit 12×RM115; T5-L109: tiga buku RM12 dan kos lima buku.
- Contoh T6-L027: 1.44 ÷ 0.6 dan anggaran; T6-L053: kad jenis risiko; T6-L071: penerbangan 22:00 UTC+8, empat jam, ketibaan zon UTC+9; T6-L081: bina sudut 50°; T6-L108: carta pai dengan sudut pusat 180°; T6-L112: dadu enam muka dan peristiwa mendapat 7.
- **409 RPH individu lain** kekal **byte-identical** dengan v55 dalam format Word/PDF/Markdown.
- **Tiada kod SK/SP, objektif, aktiviti utama, latihan BA, nombor Lesson atau rujukan sumber diubah.** Hanya seksyen set induksi 5 minit diganti pada 176 RPH.
- Selepas v56, **0/585 RPH** mempunyai **frasa generik tepat** `mengaitkannya dengan tajuk` dalam seksyen set induksi. Ini penanda aras editorial terhad, bukan pengesahan bahawa keseluruhan 585 RPH sudah lengkap akademik.

## Bukti dan ujian pada ZIP SEBENAR
- Audit **176 before/after dan petikan Aktiviti 1** berada di dalam ZIP: `AUDIT/V56_176_SET_INDUKSI_T5_T6_RPH_ONLY.csv`. CSV berasingan: `/mnt/data/math_ready_audit/matematik_v56_176_set_induksi_T5_T6_RPH_sahaja_20261107.csv`.
- **12/12 ujian** di `/mnt/data/math_ready_audit/test_v56_actual_archive.py` lulus: exact SHA, CRC ZIP, 70+106 rekod, intro unik, bukti Aktiviti 1, satu perenggan Word berubah, Markdown satu baris, 409×3 fail unchanged, **585 PDF A4 satu halaman**, **lima PDF gabungan masing-masing 117 halaman**, gate staging dan teks pembuka pada kesemua 176 PDF.
- Semua **176 Word** di-render melalui LibreOffice ke PDF. Setiap satu A4 satu halaman, teks tidak terkeluar daripada margin 15pt. Enam contoh T5-L005, T5-L053, T5-L109, T6-L055, T6-L071, T6-L108 diperiksa menggunakan contact sheet. Tiga daripadanya juga dirender dengan `render_docx.py` satu halaman.
- Hanya PDF gabungan **Tahun 5 dan 6** dijana semula ke v56; PDF gabungan Tahun 2, 3 dan 4 kekal sama byte. ZIP mengandungi **585 Word, 585 PDF individu, 585 Markdown dan lima PDF gabungan**.
- **Tiada fail RPT** ditambah ke ZIP.
- Manifest staging berhash dalam ZIP: `AUDIT/V56_RELEASE_GATE.json`. Loader pratonton terasing `rph_standalone/matematik/staging_preview_v56.py` opt-in dan SHA-locked. Ia tidak dipasang ke produksi.
- **Nota had storan:** muat naik salinan CSV audit ke Library gagal kerana **Library storage limit**; tiada fail lama dipadam. CSV masih tersedia sebagai fail perbualan dan di dalam ZIP. Hanya ringkasan checkpoint, manifest dan ujian kecil disimpan pada GitHub; ZIP besar kekal tidak awam.

## Baki yang belum selesai — HOLD
- Tiada **signoff guru akademik formal** bagi semua item latihan RPH; perbandingan 176 intro terhadap Aktiviti 1 tidak menggantikan semakan latihan asal dengan Buku Teks/Buku Aktiviti.
- **34 pasangan** pengembangan lesson Tahun 4 belum diperiksa sepenuhnya pada peringkat soalan Buku Teks.
- Belum menjalankan **Telegram–Web real staging E2E** terhadap DB kanonik; ujian ZIP dan preview mock bukan bukti keberhasilan live.
- `final_ready=false`, `rpt_changed=false`, `production_modified=false`. **Dilarang merge PR #444 atau deploy produksi** sehingga semakan akademik dan E2E sebenar lulus.
