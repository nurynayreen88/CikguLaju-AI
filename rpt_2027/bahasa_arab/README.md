# Bahasa Arab Tahun 2–6 — RPT 2027 dan RPH (staging sahaja)

**Pencapaian 5 Nov 2026:** 60 RPH Markdown **DRAF** (PdP 001–012, 12 setiap tahun), 20 unit RPT yang dikenal pasti, 60 pemetaan PdP awal serta 15 bank aktiviti Unit 2–4. **0 FINAL READY.**

- `unit_sequence_DRAF_20261105.csv`: urutan 4 unit bagi setiap tahun daripada sumber RPT 2026/buku teks; belum ditetapkan tarikh.
- `pdp_001_012_DRAF.csv`: **peta semasa utama** PdP 001–012 setiap tahun kepada SK/SP cadangan. Kolum halaman buku **FALSE** hingga audit individu.
- `pdp_001_006_DRAF.csv`: checkpoint sejarah untuk 30 PdP pertama, **bukan** sumber semasa untuk digunakan secara tersendiri.
- `rph_standalone/bahasa_arab/year2..year6/lesson_001..lesson_012.md`: 60 RPH draf, bukan dokumen siap Word/PDF.
- `materials/bahasa_arab/year2..year6/unit_02..unit_04_activity_bank_DRAF.md`: 15 cadangan aktiviti bertema untuk Unit 2–4; tidak sama dengan 15 RPH.
- `audits/bahasa_arab_stage_20261105.md`: isu sumber dan release gate.

**Belum dilakukan:** RPT 2027 A/B bertarikh, liputan PdP penuh, semakan SK/SP/halaman buku setiap PdP, Word A4 dan PDF RTL, parity generator Telegram/Web, ujian produksi dan kelulusan guru.

Jangan merge atau aktifkan fail ini melalui runtime. DB v26.00 dan rekod pengguna mesti diaudit serta disandarkan sebelum integrasi. Minggu bukan identiti PdP; tarikh A/B/cuti negeri perlu dikira berasingan.

## Indeks sumber internet terkini
- [Dokumen Google Drive rujukan Bahasa Arab Tahun 2–6](https://docs.google.com/document/d/1z5rz0j-xtIwm1JF8-p0sc5BQvk8q_W_UOZR3yFAnl7A/edit?usp=drivesdk)
- [Folder Drive rujukan](https://drive.google.com/drive/folders/1M0C9jmFvvkRIDoYB2QXJ2oQnTWUWcN9P)
- `audits/bahasa_arab_external_reference_index_20261105.json`: provenance pautan buku teks, aktiviti, DSKP, RPT; penemuan portal **bukan** pengesahan edisi/halaman.
- Fail PDF berhak cipta tidak disalin daripada internet; sumber asal boleh dibuka melalui pautan, sementara fail sedia ada dalam Drive dikekalkan.

## Bukti terbaharu Tahun 6
- Buku teks DBP/KPM 2021, ISBN 978-983-49-3300-5, julat halaman bercetak berdasarkan TOC Tahun 6: 1–30; 31–60; 61–90; 91–120.
- `audits/bahasa_arab_y6_textbook_page_evidence_20261105.json`: 12 cadangan semakan padanan PdP/halaman, satu bendera SP 2.1.1 vs buku 2.1.2/2.1.4, **bukan kelulusan RPH**.

## Pembetulan sumber 6 Nov 2026
- Tahun 3 Unit 4 rasmi **الوقت كالذهب** (Buku Teks DBP 2018, 87–117), **bukan الزمان**; yang kedua ialah tema masa. Semua sumber aktif staging (CSV dan bank aktiviti) kini menggunakan judul buku sebenar.
- Tahun 3 isi kandungan: Unit 1 (1–28), Unit 2 (29–58), Unit 3 (59–86), Unit 4 (87–117).
- Tahun 2: ISBN Buku Teks 978-983-49-1589-6, Buku Aktiviti 978-983-49-1590-2. Tahun 3: ISBN Buku Teks 978-983-49-2033-3. Semua ini identiti penerbit, **bukan sijil halaman PdP**.

## Evidence PdP awal Tahun 4
- 6/6 PdP awal Year 4 Unit 1 menerima rujukan halaman buku: **2, 2, 4–5, 3, 7, 3** dan contoh aktiviti asal. Fail `audits/bahasa_arab_y4_textbook_pdp001_006_evidence_20261106.json`.
- Bukti halaman spesifik ini **tidak** menukar status keseluruhan kepada READY; Word/PDF RTL dan kelulusan guru belum dibuat.

- Tahun 5 Unit 3 tajuk rasmi **هيا نشترك في الأنشطة اللاصفية** (kokurikulum), bukan **هيا نشترك في الأنشطة الصفية**. Sumber indeks dan bank aktiviti staging diselaraskan (6 Nov 2026).

## Audit sumber awal Tahun 5 (6 Nov 2026)
- 12 RPH PdP 001–012 bagi Unit 1 telah mendapat rujukan halaman buku dan catatan sokongan kod SP, `audits/bahasa_arab_y5_pdp001_012_source_audit_20261106.json`.
- **Bendera:** PdP 002, 004, 012 perlu semakan kandungan/SP dengan lebih teliti. Semakan halaman sumber **tidak** membuktikan RPT 2027 atau kelulusan akhir.

- Tahun 4 PdP 007–012: halaman 10,15,25,15,16,20 telah dicatat sebagai bukti sumber. `audits/bahasa_arab_y4_pdp007_012_source_audit_20261106.json`. PdP 012 perlu pembetulan kandungan individu; 12 draf Unit 1 telah menerima rujukan sumber tetapi status tetap DRAF.

## Audit Tahun 3 Unit 1 (6 Nov 2026)
- 12 PdP awal menerima bukti halaman buku bercetak dan kod SP daripada teks buku DBP/KPM 2018; fail `audits/bahasa_arab_y3_pdp001_012_source_audit_20261106.json`.
- Bersama 12 PdP Tahun 4 dan 12 PdP Tahun 5 yang telah disemak sumber, terdapat 36 PdP awal yang mempunyai audit rujukan halaman; **0 RPH FINAL READY**. PDF/Word 60 draf lulus satu A4 dalam workflow staging, tetapi bukan bukti kualiti kandungan.
