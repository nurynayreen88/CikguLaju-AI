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

## Kelayakan Penerbitan (6 November 2026)
- Ringkasan rasmi keadaan semasa: `audits/bahasa_arab_release_readiness_20261106.json`.
- **36/60** RPH draf awal Tahun 3–5 menerima semakan rujukan halaman teks sumber; Tahun 2 **0**; Tahun 6 **12 calon** (belum diluluskan individu).
- Ujian [60 DOCX + 60 PDF satu A4](https://github.com/nurynayreen88/CikguLaju-AI/actions/runs/42115776091) ialah **lulus teknikal sahaja**, bukan pengesahan kandungan atau kelulusan tahun penuh.
- Baki **15 unit** (Unit 2–4 bagi Tahun 2–6) belum mempunyai RPH individu; bank aktiviti bukan RPH. Oleh itu, **0 FINAL READY** dan PR kekal draf tanpa deploy ke Telegram/Web.

## Tahun 6 Unit 1 semakan teks (6 November 2026)
- 12 draf PdP awal menerima catatan halaman bercetak dan kod SP daripada teks buku tahun 6. PdP012 dibetulkan kepada contoh baldi pada h18. Bukti `audits/bahasa_arab_y6_pdp001_012_text_source_audit_20261106.json`.
- Kini **48/60** draf awal Tahun 3–6 mempunyai audit halaman berdasarkan teks sumber. Tahun 2 belum. Status **0 FINAL READY**.

## Tahun 2 Unit 1 — sumber buku teks asal (6 Nov 2026)
- Buku Teks DBP 2017 dengan ISBN 978-983-49-1589-6 ditemui secara teks boleh baca: https://anyflip.com/slrpb/qzcr/basic.
- PdP001–012 menerima nota halaman sumber cetak dan kod DSKP. Empat identifier SP pada **cetakan buku** masih kabur dalam OCR: 002,004,010,011; DSKP kod disahkan.
- **60/60 draf Unit 1** Tahun 2–6 kini telah diaudit pada tahap teks sumber dan mempunyai bukti halaman. Ini ialah audit awal satu unit sahaja, bukan liputan tahunan penuh atau FINAL READY.

## Tambahan Tahun 4 Unit 2 (6 Nov 2026)
- 12 RPH baharu draf PdP 013–024 berdasarkan buku asal 2019 dan DSKP Tahun 4: dengar/kenal ال, kosa kata warga sekolah, baca/tulis kata, dialog dan ayat bersambung.
- Lihat `rpt_2027/bahasa_arab/year4_unit2_pdp013_024_DRAF.csv` dan `audits/bahasa_arab_y4_unit2_pdp013_024_text_source_audit_20261106.json`.
- Unit 2 masih SEPARA; halaman 49–56 dan agihan tahunan belum diluluskan. Kini **72 RPH draf**, bukannya 72 bahan READY. Ujian Word/PDF perlu dijalankan semula untuk 72 fail.

## Tahun 4 Unit 2/3 baharu (6 Nov 2026)
- PdP025–028 Unit2 dan 029–042 Unit3 ditambah berdasarkan Buku Teks DBP/KPM Tahun4 edisi 2019, dengan SK/SP dan halaman spesifik.
- Unit2 menjadi 16 cadangan PdP; Unit3 menjadi 14 cadangan PdP. Agihan **tidak semestinya** jumlah sesi sebenar RPT 2027. Unit4 belum ada RPH individu.
- Jumlah **90 RPH DRAF**; QA struktur diselaraskan dan A4 PDF/Word perlu lulus 90 dokumen; **0 FINAL READY**.

- QA teknikal terbaharu **90 Word + 90 PDF satu halaman A4 lulus** pada [run 42124849955](https://github.com/nurynayreen88/CikguLaju-AI/actions/runs/42124849955); artifak pratonton tersedia melalui halaman workflow. Status akhir RPH **masih DRAF / 0 READY**.

## Tahun 4 Unit 4 — tambahan 16 RPH cadangan (6 Nov 2026)
- PdP043–058 bagi **بيتي جنتي** bersumber Buku Teks DBP/KPM 2019 dan DSKP Tahun 4, latihan utama h86–112. Fail `rpt_2027/bahasa_arab/year4_unit4_pdp043_058_DRAF.csv` dan `audits/bahasa_arab_y4_unit4_pdp043_058_text_source_audit_20261106.json`.
- Jumlah Year4 kini 58 RPH calon merentasi Unit 1–4. **Ini belum bermakna semua sesi tahunan lengkap** kerana pemetaan PdP rasmi RPT 2027, visual halaman dan semakan guru belum selesai.
- 106 RPH DRAF dalam keseluruhan staging; Word/PDF 106 perlu diuji; 0 FINAL READY.

- [CI teknikal 106 Word + 106 PDF satu halaman A4 telah lulus](https://github.com/nurynayreen88/CikguLaju-AI/actions/runs/42127983356), pratonton tersedia sebagai artifak GitHub; kelulusan pedagogi masih belum dibuat dan PR kekal draft.

## Tahun 5 Unit 2 — 16 RPH baharu (6 Nov 2026)
- Unit **ما ألذ الطعام!** PdP013–028, 16 draf berdasarkan buku Tahun5 2020 halaman 30–56; peta `rpt_2027/bahasa_arab/year5_unit2_pdp013_028_DRAF.csv`; bukti `audits/bahasa_arab_y5_unit2_pdp013_028_text_source_audit_20261106.json`.
- Kini **122 RPH draf** dalam staging, bukan 122 READY. Tahun5 Unit3/4 belum ada RPH individu; turutan RPT 2027, kelulusan per PdP, fon Arab dan PDF akhir perlu disemak.

- [122 RPH Word/PDF satu halaman A4 lulus dalam CI](https://github.com/nurynayreen88/CikguLaju-AI/actions/runs/42131146183). Ini ujian format teknikal, bukan pengesahan kualiti Arab, padanan RPT 2027 atau kebenaran penerbitan. 0 READY.

## Tambahan Tahun5 Unit3 (6 Nov 2026)
- 16 RPH calon PdP029–044 bertema kokurikulum (Unit3: **الأنشطة اللاصفية**), halaman Buku Teks 58–84, bersama CSV dan audit `audits/bahasa_arab_y5_unit3_pdp029_044_text_source_audit_20261106.json`.
- Staging kini 138 RPH DRAF; unit4 Y5 masih tiada RPH, RPT 2027/kelulusan individu belum disahkan. Ujian A4 138 dokumen perlu dijalankan.

- [Ujian teknikal 138 RPH Word + PDF A4 berjaya](https://github.com/nurynayreen88/CikguLaju-AI/actions/runs/42132565716). Kemahiran Arab, sumber visual, susunan RPT 2027 dan kelulusan PdP demi PdP belum FINAL READY.

## Tahun 5 Unit 4 (6 November 2026)
- 16 draf baharu PdP045–060 Unit **رفقا بالحيوانات!** berdasarkan latihan buku teks DBP/KPM 2020 pp86–110 dan kod SP cadangan; peta `year5_unit4_pdp045_060_DRAF.csv` dan bukti `audits/bahasa_arab_y5_unit4_pdp045_060_text_source_audit_20261106.json`.
- 154 RPH keseluruhan, 60 Tahun5 merentasi empat unit, **0 FINAL READY**. RPT 2027/Kumpulan A/B dan kelulusan guru belum selesai. CI 138 lulus; tambahan sehingga 154 belum diujikan A4.
- Cabang semakan berasingan; tiada deploy Telegram/Web/DB.
