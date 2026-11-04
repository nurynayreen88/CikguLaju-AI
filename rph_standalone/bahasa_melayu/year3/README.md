# CikguLaju AI — RPH Standalone Bahasa Melayu Tahun 3 (2027)

**STATUS: 165/165 fail RPH tersedia • 162 DRAF • 3 HOLD • 0 READY (semakan 4 November 2026).**

## Liputan

- `lesson_001.md` hingga `lesson_165.md` disimpan sebagai RPH berasingan dengan ID BM3-P001 hingga BM3-P060.
- Komponen setiap RPH: fokus, objektif terukur, tindakan guru, tindakan murid, bahan, set induksi, dua aktiviti utama, pengukuhan/PBD dan penutup.
- Latihan BA dirujuk daripada [Buku Aktiviti Bahasa Melayu Tahun 3 Jilid 1, DBP 2018](https://drive.google.com/file/d/1WoaWY-FgDVhJTZjQI16T3Ol6jFvmlGOg/view). Untuk 001–060, tajuk Buku Teks **tidak dianggap sama** dengan tajuk BA jika berlainan.
- [DSKP BM Tahun 3 SK](https://drive.google.com/file/d/1q-Mdq8kIZGui7-IccvSGJx1dfMjIOAQN/view) mengawal makna SP dan subkod. RPT 2026 merupakan susunan rujukan: [dokumen](https://docs.google.com/document/d/1wlrI120RKhZh85oSPIZPPgJwj7CKChsT/edit).
- Fail [Buku Teks BM Tahun 3 Jilid 1](https://drive.google.com/file/d/1XzZLY895kPRmzWmN-WuOuJnfAX38_tEe/view) telah dikenal pasti, tetapi **tidak dapat diteliti teks penuhnya** melalui sambungan semasa. Jangan mendakwa semua aktiviti BT sudah disahkan.

## Status HOLD

- **Lesson 001–030 (8):** 003, 007, 013, 015, 022, 023, 024, 030. Punca: PKJR; cadangan pengukuhan; pemulihan/pengayaan; subkod SP gabungan tidak sepenuhnya dibuktikan oleh BA.
- **Lesson 031–045 (8):** 034, 036, 037, 041, 042, 043, 044, 045. Punca: latihan BA tidak menyokong semua subkod; tugasan berulang; pengesahan BT/PKJR masih berbaki.
- **Lesson 046–060 (9):** 046, 047, 049, 053, 054, 055, 056, 057, 058. Punca: sumber BT belum disahkan, konflik 2.1.1(i)/2.2.1(i) pada BA m/s 48, sesi berulang atau HP PKJR.
- **Jumlah: 25 HOLD**. Tiada rekod ini dipadam; tiada kod SP rasmi dicipta.

## Laporan dan pengujian

- [Audit 001–030](../../../rpt_2027/bahasa_melayu/AUDIT_BA_DSKP_BM_T3_001_030_20261103.md) dan [audit 031–060](../../../rpt_2027/bahasa_melayu/AUDIT_BA_DSKP_BM_T3_031_060_20261103.md).
- [RPT Tahun 3](../../../rpt_2027/bahasa_melayu/keluaran_format_english/RPT_BM_TAHUN_3_2027_A_B_PER_LESSON_DRAF.md), 165 calon Lesson, 44 minggu, MD/HTML padanan lengkap selepas pembetulan.
- **60/60** fail telah disemak secara langsung untuk padanan metadata RPH–RPT dan struktur wajib; **0 percanggahan**.
- Ujian Python `python tools/qa_bm_2027_readiness.py rph` ada tetapi **belum dijalankan di CI/runtime**; pemeriksaan fail dalam sambungan GitHub tidak sama dengan ujian produksi.
- [Pintu penerbitan](../../../rpt_2027/bahasa_melayu/READY_GATE.json) masih `DRAFT_NOT_PUBLISHED`. Tahun 3 mempunyai `rph_all_present=false` sehingga 165/165 fail ada dan sumber/semakan lulus.

**Baki Tahun 3:** 3 HOLD memerlukan keputusan akademik khusus; semua 165 fail sudah tersedia. Semakan satu halaman A4, kalendar negeri, QA/CI dan pembacaan Telegram belum lulus.


## Semakan Buku Teks Jilid 1 pada 4 November 2026

19 Lesson diperiksa semula dengan BT1, BA1 dan DSKP. Kesilapan padanan SP pada 034, 043, 049, 054, 076–080 dan 094 telah dibetulkan dalam RPT serta RPH. Tajuk/halaman BT pada 042, 045, 082, 083, 088, 089, 090 dan 092 dipulihkan. 089 kekal HOLD bagi PKJR; Lesson 072, 093 dan 094 dilabel jelas sebagai pengayaan/pengukuhan/penilaian. Kiraan semasa selepas batch susulan 159 DRAF, 3 HOLD, 0 READY, tidak membayangkan telah lulus penerbitan.

## Audit terarah BT1 / BA1 — Batch kedua, 4 November 2026

16 Lesson 007, 013, 015, 022–024, 030, 036–037, 041, 046–047, 053, 055–057 telah dikemas kini berdasarkan BT1 dan BA1. Pembetulan subkod kritikal: 024 menjadi 1.1.2(i), 030 menjadi 2.1.2(ii). Lesson pemulihan, pengayaan, penilaian dan Bacaan Luas dilabel jelas. Status terkini **159 DRAF, 3 HOLD, 0 READY**.

## Buku Teks Jilid 2 — Audit 24 Lesson, 4 November 2026

23 Lesson diselaraskan daripada HOLD kepada DRAF menggunakan Buku Teks dan Buku Aktiviti Tahun 3 Jilid 1/2 (SK). Lesson 116 kekal HOLD kerana RPT 2026 menyatakan +PKJR, yang dipulihkan pada tajuk. Subkod Lesson 138 dibetulkan kepada 1.1.3(i) berdasarkan BT2 m/s51. **159 DRAF, 3 HOLD, 0 READY**. Lihat laporan audit BT2. Ini bukan kelulusan pemasangan ke Telegram.

## Audit PKJR menyeluruh — 4 November 2026

RPT BM Tahun 3 SK 2026 mengandungi 28 penanda +PKJR, sedangkan staging sebelum semakan hanya 19. Sembilan penanda bagi Lesson 009, 010, 019, 030, 035, 040, 094, 096, 101 telah dipulihkan. Dua Lesson sedia bertanda PKJR (050, 075) juga dikategorikan HOLD sehingga pemetaan modul disahkan. Kini **159 DRAF, 3 HOLD, 0 READY**. Dokumen silang rujuk HP/BAM dibina berasingan.

## Audit PKJR BAM 28 Lesson — 4 Nov 2026

Semua 28 RPH PKJR kini mempunyai aktiviti khusus 10 minit, arahan guru dan murid, PBD, rujukan BAM. **22** kembali DRAF; enam HOLD (003, 010, 079, 089, 094, 157) akibat konflik kod/aktiviti atau ulang sesi. Status **159 DRAF, 3 HOLD, 0 READY**. Pembetulan BT Jilid2: 107,112,125,139,151. A4/kalendar/CI dan BPG belum lulus. Jangan terbitkan ke Telegram.

## Pemutihan tiga padanan PKJR (4 November 2026)

Lesson 003: HP 1.1.1 mengenal kenderaan disokong kandungan BAM Aktiviti 1. Lesson 010: RPT2026 Aktiviti 2B ialah bahagian B BAM Aktiviti 2 m/s3, bukan aktiviti baharu. Lesson 157: HP asal 4.3.1 tidak padan BAM22 m/s24 alat penahan, dipetakan kepada **HP 6.2.1** berdasarkan BPG/BAM. Ketiga-tiganya DRAF, **bukan READY**. Hanya Lesson 079, 089 dan 094 kekal HOLD. Status semasa **162 DRAF, 3 HOLD, 0 READY**.
