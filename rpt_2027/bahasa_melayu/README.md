# CikguLaju AI — RPT Bahasa Melayu SK 2027

**STATUS: FORMAT GURU TAHUN 2–6 TELAH DISIAPKAN DALAM STAGING, KANDUNGAN BELUM READY.**

## Keluaran utama — format RPT English 2027 (gabungan A dan B)

Setiap tahun mempunyai satu RPT berstruktur **Minggu → Lesson/PdP bernombor**, setiap Lesson pada baris tersendiri. Kolum: Tema/Unit, aktiviti, SK, SP, rujukan Buku Teks/Buku Aktiviti dan Catatan/PBD. Julat minggu Kumpulan A/B digabungkan pada satu tajuk minggu.

| Tahun | Unit | Lesson calon | RPT untuk cetak (HTML) | RPT untuk semak (MD) |
|---|---:|---:|---|---|
| 2 | 24 | 164 | [Buka HTML](keluaran_format_english/RPT_BM_TAHUN_2_2027_A_B_PER_LESSON_DRAF.html) | [Buka Markdown](keluaran_format_english/RPT_BM_TAHUN_2_2027_A_B_PER_LESSON_DRAF.md) |
| 3 | 24 | 165 | [Buka HTML](keluaran_format_english/RPT_BM_TAHUN_3_2027_A_B_PER_LESSON_DRAF.html) | [Buka Markdown](keluaran_format_english/RPT_BM_TAHUN_3_2027_A_B_PER_LESSON_DRAF.md) |
| 4 | 27 | 165 | [Buka HTML](keluaran_format_english/RPT_BM_TAHUN_4_2027_A_B_PER_LESSON_DRAF.html) | [Buka Markdown](keluaran_format_english/RPT_BM_TAHUN_4_2027_A_B_PER_LESSON_DRAF.md) |
| 5 | 27 | 166 | [Buka HTML](keluaran_format_english/RPT_BM_TAHUN_5_2027_A_B_PER_LESSON_DRAF.html) | [Buka Markdown](keluaran_format_english/RPT_BM_TAHUN_5_2027_A_B_PER_LESSON_DRAF.md) |
| 6 | 27 | 165 | [Buka HTML](keluaran_format_english/RPT_BM_TAHUN_6_2027_A_B_PER_LESSON_DRAF.html) | [Buka Markdown](keluaran_format_english/RPT_BM_TAHUN_6_2027_A_B_PER_LESSON_DRAF.md) |

**Jumlah: 825 Lesson calon, 129 unit; 44 minggu M01–M44 setiap tahun.** [Indeks lengkap keluaran format English](keluaran_format_english/README.md). Cetak A4 landscape dengan fail HTML (muat turun raw dari GitHub dahulu).

## Tahun 1 — berasingan KP2027

DK Bahasa Melayu SK Tahun 1 dan buku baharu KP2027 belum disahkan dalam indeks sumber projek. Jangan mengisi RPT Tahun 1 2027 daripada DSKP dan RPT BM 2026 lama. [RPT induk KP2027](https://docs.google.com/document/d/1qLMeq2Ff3KMwC_lFBRYfL1DoAXKbzWNaV38t4et3MIU/edit).

## Audit utama dan bahan kerja terdahulu

- [Audit RPT BM SK 2027](AUDIT_RPT_BM_2027_20261103.md): penjelasan SP, status sumber, Buku Aktiviti dan tarikh.
- [Audit sambungan 3 Nov — 57 pembetulan dan keselarasan 825 Lesson](AUDIT_PEMBETULAN_SP_DAN_FORMAT_20261103_B3.md): semakan format Markdown/HTML Tahun 2–6, pembetulan daripada RPT 2026, baki sebelum READY.
- [Audit global 825 Lesson](AUDIT_ULANGAN_GLOBAL_825_20261103.md): 37 pasangan padanan merentas minggu, termasuk 6 varian +PKJR. Tiada Lesson dipadam.
- [Audit pengulangan terdahulu](AUDIT_PENGULANGAN_19_BM_2027.md): semakan awal 19 bendera (12 calon sama tajuk, 7 berbeza aktiviti) — **digantikan oleh audit global** untuk kiraan ulangan.
- [Audit pembetulan SP batch 4](AUDIT_KUALITI_BM_2027_SP_DSKP_BATCH4.md): 34 pembetulan ayat SP terpotong + 36 pelengkapan subkemahiran DSKP T2/T3, format MD–HTML kekal sama.
- [Kalendar Kumpulan A](kalender_kumpulan_A_2027_44_minggu_INDUK.md) dan [Kumpulan B](kalender_kumpulan_B_2027_44_minggu_INDUK.md).
- Matriks PdP A/B berasingan dan draf asal dalam folder ini dikekalkan sebagai rekod audit; **bukan keluaran utama untuk guru**.

## Sumber utama

- [RPT induk semua subjek 2027](https://docs.google.com/document/d/1MO37hjLMT5Afzlnq2--rf3jJQKX9BlTdyejZvU6Yau4/edit).
- [Indeks sumber BM SK Tahun 1–6](https://docs.google.com/document/d/1T7RnqWaB5WZsrB3nUg07T3tf0nyER25NhtdNOc9LeMc/edit).
- [Kalendar minggu & cuti negeri 2027](https://docs.google.com/spreadsheets/d/1tf6-B6hmA4U6E0fCROcKpxh-B5uLUQOYBt6TZft_7_k/edit).

## Audit lanjutan — 164 RPH BM T2 (3 Nov 2026)

- **RPH Standalone BM Tahun 2: 164/164 fail**, semua fail telah diaudit satu-persatu untuk tajuk, SK, SP dan komponen wajib. Selepas pembetulan, **0 percanggahan metadata/struktur**.
- Status kandungan: **135 DRAF, 29 HOLD, 0 READY**. Kumpulan berstatus HOLD tidak boleh diterbitkan kepada guru.
- [Laporan audit penuh 164 RPH](AUDIT_RPH_BM_T2_164_20261103.md) • [Indeks fail RPH](../../rph_standalone/bahasa_melayu/year2/README.md).
- Manifest `READY_GATE.json` kini menyatakan `rph_all_present=true` **untuk Tahun 2 sahaja**, sementara semua pintu akademik/BA/kalendar/cetakan/runtime lain masih false.
- Arahan semakan baharu: `python tools/qa_bm_2027_readiness.py rph` (semak metadata RPH-RPT; **belum diuji di CI**). Semakan READY kekal fail-closed.
- Audit struktur RPT Tahun 2–6 dalam staging: 825/825 Lesson, 44 minggu setiap tahun, pasangan Markdown–HTML sepadan. Ini bukan kelulusan kandungan atau penerbitan.

## Kemajuan RPH dan audit sumber primer — 3 Nov 2026

- [RPH Standalone BM Tahun 2 — Lesson 001–010](../../rph_standalone/bahasa_melayu/year2/README.md) telah disimpan sebagai **10 DRAF, 2 HOLD PKJR, 0 READY**. Ini bahan berasaskan buku teks, belum dipaparkan untuk guru.
- Buku Aktiviti BM Tahun 3 SK Jilid 1 ([sumber](https://drive.google.com/file/d/1WoaWY-FgDVhJTZjQI16T3Ol6jFvmlGOg/view)) dan Jilid 2 ([sumber](https://drive.google.com/file/d/1ln3x1r0kXSXIBJObUIG1iUaas0jGFkt0/view)) berjaya dibaca. Pembetulan rujukan BA1 bagi BM3-P005, P011, P012 dan P016 telah dibuat selepas silang kod SP dengan kandungan BA; audit halaman lain belum selesai.
- [Manifest READY](READY_GATE.json) menyekat status penerbitan, manakala [QA RPT/RPH BM](../../tools/qa_bm_2027_readiness.py) menguji struktur dan kelengkapan sebelum layak diterbitkan.
## Pintu READY

Semak kod dan teks SK/SP serta subkod dengan DSKP asal, halaman BT/BA dan aktiviti sebenar, 12 rekod pengulangan, cuti dan ganti mengikut negeri, slot masa sekolah, dan tahun peperiksaan sebelum keluaran akhir. Word DOCX akhir dan RPH standalone BM belum diterbitkan. Fail ini disimpan dalam branch staging, `main`, DB, Telegram dan Web tidak diubah.
