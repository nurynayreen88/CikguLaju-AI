# RPT 2027 — audit jurang sumber dan kemajuan pembetulan (7 Nov 2026)

**STAGING SAHAJA.** PR #441 kekal draf. Penyelarasan format 56 PDF telah lulus checkpoint lama, tetapi **belum READY** dari segi kesahihan kandungan, jadual negeri dan Web/Telegram.

## 1. Sains Tahun 2–6

Pangkalan standard v26.00 yang disahkan mengandungi **422 kod SP berbeza**, dan snapshot PdP bernombor v25.82 hanya memperlihatkan **342** daripadanya. Pecahan:

| Tahun | Kod SP disahkan | SP diwakili dalam PdP lama | Tidak diwakili |
|---|---:|---:|---:|
| 2 | 51 | 51 | 0 |
| 3 | 45 | 45 | 0 |
| 4 | 110 | 79 | 31 |
| 5 | 107 | 83 | 24 |
| 6 | 109 | 84 | 25 |
| **Jumlah** | **422** | **342** | **80** |

**Penting: 80 kod bukan 80 PdP.** Audit lanjut mengelaskan **51 kod** sebagai kemahiran merentas kandungan (SK 1.1 Kemahiran Proses Sains, SK 1.2 Kemahiran Manipulatif, setiap satu 12+5 SP bagi Tahun 4, 5 dan 6) dan **29 kod** sebagai topik sebenar yang belum muncul dalam snapshot PdP (Y4=14, Y5=7, Y6=8). KPS mesti dipautkan kepada aktiviti sebenar, bukan diluluskan secara pukal.

Sumber machine-readable: `scripts/audit_sains_rpt2027_uncovered_verified_sp_staging.py`. Output JSON bertajuk `sains_verified_sp_coverage_gap_20261107_DRAF.json` disimpan dalam artifak CI RPT Sains. Laporan menyimpan semua kod, teks SK/SP yang telah disahkan serta halaman sumber bagi 35 SP KPM tambahan. **Tiada PdP baharu direka, tiada kebenaran menerbitkan diberikan.**

## 2. RBT Tahun 4–6

96 PdP mempunyai identiti, sumber kod SK/SP serta rujukan buku calon. Tiada sumber sekolah yang menetapkan minggu 2027 bagi semua PdP. Tujuh blok minggu asal RPT **2026** diperoleh bagi **23 kod SP** (T4=6, T5=10, T6=7). Pemetaan ini dicatat pada nota PDF staging sahaja dan jelas disebut **BUKAN tarikh 2027**; satu blok projek boleh merangkumi beberapa minggu/SP.

Penjana opt-in `rpt_2027/common/rbt_teacher_week_allocation_staging.py` menerima tepat **32 pilihan PdP→minggu** setiap tahun dengan medan `academic_year=2027`, `year`, `status=EXPLICIT_TEACHER_SUGGESTION_NOT_RELEASE_SIGNOFF`, `school_calendar_verified=false`, `source_reference` dan `pdp_to_week`. Ia:
- Menolak status READY, tahun salah, minggu di luar KPM, duplikasi ID, urutan mengundur dan input separa.
- Mengambil julat Kumpulan A dan B hanya daripada kalendar induk yang sama, bukan daripada RPT 2026.
- Boleh menjana PDF **STAGING** berasingan dengan `build_teacher_rbt_preview`; tidak mengganti 56 fail asas atau jadual pengguna.

**Tiada jadual sekolah individu telah disediakan**, maka 96 PdP asas masih mempunyai minggu kosong (betul dan selamat); opsyen ini membolehkan penjadualan selepas input sebenar.

## 3. Pendidikan Islam Tahun 2/6

Enam baris RPH V5 asal dikekalkan sebagai **DITAHAN**; keenam-enam slot RPT berjaya dijejak kepada Google Doc RPT sumber:
- T2 L035: Tasmi' Al-Baqarah 224–245, minggu calon M14.
- T6 L006: Tasmi' Asy-Syura 33–77, M03.
- T6 L014: Tasmi' Az-Zukhruf 34–73, M05.
- T6 L018: Tasmi' Ad-Dukhan 40–59, M06.
- T6 L060: M18, **konflik kod SK 4.2 antara kandungan Tahun 5 Solat Berjemaah yang tersalin dalam RPT sumber Tahun 6 dan SK 4.2 Tahun 6 Solat Ketika Sakit**. Rekod L059 V5 sudah memegang Tahun 6 Solat Ketika Sakit SP4.2.3–5, maka perlu semak pertindihan aktiviti sebelum mencipta RPH L060.
- T6 L117: Tasmi' beberapa petikan Juz29, M36; urutan juz/ayat memerlukan pengesahan.

Lima tasmi' tidak dibekalkan dengan kod SK/SP rasmi dalam sumber. Tiada kod direka, dan **semua enam RPH V5 masih ditahan**. Bukti: `audits/pendidikan_islam_rpt2027_6_held_source_recovery_20261107_DRAF.json`, ujian `tests/test_pi_rpt2027_6_held_source_recovery_staging.py`. Google Docs sumber T2 dan T6 seperti dalam ledger. Bukti tambahan konflik Tahun 5/6: laman sekolah KPM Tahun 6 Solat Ketika Sakit https://sites.google.com/moe-dl.edu.my/gapd-rukhsah-solat/utama dan bahan Tahun 5 Solat Berjemaah https://edu.sistemguruonline.my/wp-content/uploads/2023/11/carta-alir-SOLAT_BERJEMAAH_MEMBENTUK_KEKUATAN_UMMAHSOLAT_JEMAAH_.pdf .

## 4. Bahasa Arab Tahun 2–6

**298/298 PdP** telah diberi rujukan halaman PDF DSKP untuk setiap kod SP, merangkumi **117/117 kod SP unik**. Rujukan halaman dan cap SHA-256 tersedia dalam `audits/bahasa_arab_rpt2027_y2_y6_117_sp_pdf_page_evidence_20261107.json`. Susunan Latin/Arab dalam jadual PDF telah diperbaiki.

**Pernyataan teks SK/SP Arab penuh belum diluluskan**, kerana kerosakan glyph/atur tulisan RTL sewaktu pengekstrakan PDF. Kekalkan placeholder dan elak menukar terjemahan/cadangan menjadi DSKP rasmi.

## 5. Gate penerbitan yang kekal

`scripts/audit_rpt2027_release_gaps_staging.py` dan ujiannya menghasilkan laporan JSON pembaca mesin, sentiasa `is_release_ready=false`. Baki:
1. Semakan perkataan Arab DSKP sebenar, halaman buku dan aktiviti setiap PdP.
2. Keputusan akademik perihal tasmi' pilihan guru dan L060 Ibadah Tahun 6.
3. Pemetaan 51 KPS kepada aktiviti sebenar, dan 29 SP Sains topik kepada RPH/buku teks.
4. Penyediaan jadual sekolah sebenar RBT dan pelarasan cuti negeri Kumpulan A/B.
5. Ujian pengguna berdaftar, identiti kelas, ZIP/Word/PDF, muat turun serta kesetaraan sumber Web–Telegram.

**JANGAN MERGE/DEPLOY ATAU UBAH `main`/DB** sehingga bukti akademik, kalendar, kerja sekolah dan ujian E2E semuanya diluluskan.
