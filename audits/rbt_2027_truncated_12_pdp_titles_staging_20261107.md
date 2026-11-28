# RBT 2027 — 12 tajuk PdP terpotong pada rekod lama

**Tarikh:** 7 November 2026. **Skop: tajuk paparan RPT PDF staging sahaja.**

Semasa audit RPT RBT T4–T6, 12 daripada 96 tajuk PdP didapati terhenti pada sempadan lama **99 aksara**; sebahagiannya terpotong di tengah perkataan, sehingga paparan kelihatan tidak siap. Kod SK/SP adalah betul, tetapi tajuk asal dari CSV/RPH tidak lengkap. Tiada ayat baharu dikarang untuk menampal kekurangan ini.

| Tahun | PdP yang mempunyai tajuk terpotong | Bilangan |
|---|---|---:|
| 4 | 003, 017, 019, 021, 028, 030 | 6 |
| 5 | 005, 010, 014, 029 | 4 |
| 6 | 018, 022 | 2 |
| **Jumlah** | | **12** |

**Pembetulan dalam PR #441:** `rpt_2027/common/rbt_truncated_title_guard_staging.py` menggunakan **pernyataan penuh SP pertama daripada DSKP sumber asal** untuk menggantikan *tajuk paparan PDF sahaja* apabila judul CSV yang panjangnya 99 aksara didapati awalan tidak lengkap, atau mempunyai sambungan yang terpotong selepas pernyataan SP asal. Nilai asal disimpan dalam `source_topic`. Penanda `FULL_DSKP_SP_EXACT_STAGING_ONLY` menunjukkan pembetulan paparan, **bukan kelulusan pedagogi**.

Pengecualian penting: PdP T4-028 mempunyai tajuk yang bermula dengan pernyataan penuh SP 6.1.6 diikuti fragmen penjelasan “Pseudokod ialah satu set pernya...”. Pengganti paparan ialah pernyataan SP rasmi **6.1.6** sahaja; maklumat yang terpotong tidak disambung secara rekaan.

**Pagar kualiti:** menguji tepat 12 identiti PdP, teks SP rasmi sepadan dengan paparan, 84 tajuk lain tidak berubah, urutan 96 PdP, sumber CSV/RPH asal, dan semua tarikh/label jadual yang belum sah. Generator berhenti dengan ralat jika hitungan atau susunan sumber berubah. Fail PDF staging dan simulasi diuji melalui GitHub Actions.

**Masih perlu keputusan berasingan:** adakah tajuk dalam RPH asal (bukan hanya paparan RPT) patut diperbetul? Skrip ini **tidak** menimpa JSON RPH sumber, Web, Telegram atau DB. Pembersihan RPH mesti dibuat dalam versi berasingan dengan audit integriti dahulu.
