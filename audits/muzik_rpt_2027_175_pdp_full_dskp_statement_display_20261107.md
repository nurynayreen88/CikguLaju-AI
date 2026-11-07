# Pendidikan Muzik Tahun 2–6 — SK/SP berpernyataan DSKP untuk RPT 2027

**Tarikh:** 7 November 2026  
**Skop:** lima PDF RPT dalam PR #441, **staging sahaja**, bukan RPH atau kandungan produksi.

## Kaedah yang dilakukan

Saya membaca kelima-lima DSKP Muzik KPM dari Google Drive pengguna, semak lajur *Standard Kandungan* dan *Standard Pembelajaran* dalam PDF asal, keluarkan klausa teks mengikut kod, dan simpan pada fail crosswalk `staging/pendidikan_muzik/rpt_rph_2027/DSKP_MUSIC_FULL_TEXT_Y{2..6}_20261107_DRAF.json`. Setiap item menyimpan kod SP, kod & tajuk SK, teks rasmi yang dapat diekstrak, nombor halaman PDF dan bendera jika notasi/skor grafik tidak lengkap dalam lapisan teks. SHA256 PDF asal disimpan dalam setiap ledger.

| Tahun | Kod SP DSKP dibaca | PdP RPT dengan SP asal | SP DSKP yang tidak diperuntukkan PdP |
|---|---:|---:|---|
| 2 | 20 | 35 | 2.3.1 |
| 3 | 22 | 35 | 2.4.3 |
| 4 | 19 | 35 | Tiada |
| 5 | 20 | 35 | Tiada |
| 6 | 18 | 35 | Tiada |
| **Jumlah** | **99 entri kod-tahun** | **175** | **2 entri sumber** |

Kesemua kod SP dalam **175 PdP RPT asal** mempunyai padanan kod dan klausa SP dalam DSKP; pernyataan SK kini turut diambil daripada tajuk SK rasmi bercetak mengikut DSKP tahun yang sama.

## Amaran sumber yang tidak boleh ditutup secara rekaan

1. DSKP Tahun 2 mencetak label SK *Elemen Muzik* sebagai `1.1.1`, sedangkan SP di bawahnya `1.1.1–1.1.4`; lajur SK paparan menggunakan `1.1 — Elemen Muzik` dan mencatat percanggahan nombor bercetak. **Jangan ubah DSKP asal.**
2. DSKP Tahun 4 mencetak **SK 3.1 Pengkaryaan Muzik** bersama **SP 3.2.1–3.2.3**, dan **SK 4.1 Penghayatan Karya Muzik** bersama **SP 4.2.1**. Ketidakselarasan nombor dicatat terang dalam nota RPT. Ia tidak dinormalkan senyap.
3. Beberapa SP Tahun 2–6 memuatkan **notasi muzik, skor, gambar atau ikon** yang tidak diwakili sempurna dalam lapisan teks. Pernyataan bertulis disertai nota `rujuk rajah DSKP PDF hlm...`, bukannya simbol muzik rekaan.
4. Pemetaan DSKP ke PdP/RPT ialah **pemeriksaan kod & paparan teks**. Ia bukan kelulusan skor/audio/buku teks bagi 175 aktiviti.

## Perlindungan keluaran staging

- Fail sumber `RPT_MUZIK_TAHUN_*_2027_DRAF.csv`, semua 175 RPH, database, Telegram dan Web **tidak diubah**.
- Generator `scripts/build_rpt_2027_remaining_four_subjects_staging.py` kini memperkaya `sk_display`/`sp_display` serta mengekalkan `source_rpt_sp_codes`.
- Enjin `rpt_2027/common/music_dskp_full_statement_staging.py` akan gagal jika sumber kekurangan kod, SHA format rosak, tajuk SK bercanggah, kod berulang, atau halaman sumber luar julat.
- Ujian `tests/test_rpt_2027_music_full_dskp_statements_staging.py` memaksa 175 PdP dan 99 kod/tahun, termasuk dua SP sumber yang tidak digunakan serta isu nombor asal Tahun 4.

**Status:** RPT Muzik **SK/SP tekstual diselaraskan ke DSKP** selepas CI lulus. **Belum FINAL READY:** audio, notasi visual, rujukan buku, keselamatan aktiviti, jadual sekolah dan integrasi aplikasi masih perlu audit substantif.

Sumber:
- T2: https://drive.google.com/file/d/1e68JHJagmLzcQdodb9IAIvYFtKIybtiu/view
- T3: https://drive.google.com/file/d/1uu1n3V3dL5aN0MCC7gdwaG6II1nGJWFz/view
- T4: https://drive.google.com/file/d/1C0e_KVtPA3bx7dlFiFEaAyT94RWzQVob/view
- T5: https://drive.google.com/file/d/1lR2irHRk8B0wqy5Y6nb8O8DRsOA9GRnY/view
- T6: https://drive.google.com/file/d/1xvgqs4L35uaTFJ0foencmAO4_pVR-g19/view
