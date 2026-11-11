# Matematik v50 — pembetulan kandungan sebenar (7 November 2026)

**KEPUTUSAN:** 585/585 RPH kekal lengkap; QA teknikal **PASS**. Empat RPH dibetulkan pada aras aktiviti/soalan; **FINAL READY akademik kekal NO**. Cabang `staging/matematik-ba-evidence-20261107` sahaja.

## Punca yang disahkan dengan sumber

**A. Tahun 2 Lesson 111 dan 112, SP 7.3.1 (7.0 Ruang).**
- RPH v49 mengajar **carta palang/jadual data**, sedangkan SP 7.3.1 berada dalam unit Ruang dan Buku Aktiviti Matematik Tahun 2, halaman bercetak **145–146**, mempunyai masalah **bentangan kubus, ciri silinder, segi empat tepat, piramid**.
- Halaman BA 145–146 diperiksa secara **visual** pada PDF asal (printed+6 = PDF pages 151–152). Kedua-dua footer mencatat **SP 7.3.1** dan rujukan Buku Teks Matematik Tahun 2 **hlm. 88–89**.
- Set induksi, Aktiviti 1, Aktiviti 2, PBD dan BBM dibetulkan kepada **geometri 2D/3D**. Kedua-dua lesson dibezakan: L111 penerokaan/model dan L112 latihan kendiri/pentaksiran susulan. Rujukan diperkemas kepada BA p145–146 dan BT p88–89, tanpa mengandaikan mana-mana item telah diberi kelulusan guru.

**B. Tahun 4 Lesson 109, SP 8.1.1.**
- DSKP Tahun 4 Bab 8.0 Pengurusan Data SP 8.1.1 menghendaki **membina piktograf dan carta palang daripada data tak terkumpul**.
- RPH v49 hanya menyusun jadual kekerapan; ia tidak memenuhi kaedah pembinaan carta pada aktiviti utama atau PBD.
- v50: aktiviti buah 20 murid kini menghasilkan **piktograf**; aktiviti pengangkutan 15 kad menghasilkan **carta palang**, dengan tajuk, paksi dan skala; PBD menguji kedua-dua carta berasaskan data ringkas. Tajuk/objektif/SP/urutan lesson dikekalkan.

**C. Tahun 4 Lesson 114, SP 8.1.2.**
- RPH v49 menyatakan kategori C=5 ikon, B=3 ikon, 1 ikon=2 buku, tetapi menulis beza sebagai **4 ikon = 8 buku** dan seterusnya **4 buku**.
- v50 membetulkan jalan kerja kepada **5−3 = 2 ikon, 2×2 = 4 buku**; keseluruhan aktiviti lain dikekalkan.

## Artifak/semakan
- Sumber: `CIKGULAJU_MATEMATIK_v49_585_RPH_KADAR_RM1_DAN_MASA_STAGING.zip`, SHA256 `fcc3e7fe07ed6eb9cb0abdff1ef3bd1765c7050a6d8e036b81abd199ae4835b0`.
- Hasil: `CIKGULAJU_MATEMATIK_v50_585_RPH_GEOMETRI_DAN_GRAF_STAGING.zip`; **48,769,382 bait**, SHA256 `895c87161dd7b62d9cecdea20b1d9efdf7ce0b77a14915d4edc186c4d2c9cdbb`.
- **4 RPH** berubah pada **16 seksyen**; **12 fail individu** (4 Word, 4 PDF, 4 Markdown) diubah. **581 RPH lain adalah byte-identical** berbanding v49. PDF gabungan Tahun 2 dan Tahun 4 dijana semula.
- ZIP `testzip() == None`; **585/585 PDF** kekal satu halaman A4. 4 dokumen Word dirender menjadi PDF lalu PNG, diperiksa visual; tiada teks terpotong/lepas sempadan halaman.
- **21/21 ujian pratonton setempat menggunakan ZIP v50 SEBENAR** PASS: 585 PDF boleh dibaca, ekstrak Word yang tepat, hash fail, autorisasi admin/berbayar, status gagal penghantaran, tiada DB/kuota/pembayaran, callback lama terus bekerja. **Ini bukan Telegram/Web staging live E2E**.
- Audit perubahan dalam `audits/matematik_v50_4_rph_16_section_semantics_20261107.csv`; manifest dalam `audits/matematik_v50_release_gate_20261107.json`.
- Loader pratonton `rph_standalone/matematik/staging_preview_v50.py` **opt-in sahaja**, hash v50 dikunci dan `final_ready=false` dituntut.
- **Tiada scan halaman buku dimuat naik ke GitHub awam**; hanya ringkasan bukti dan aktiviti yang dicipta semula.

## Halangan penerbitan
- Signoff akademik formal untuk latihan BA/BT individu pada semua 585 RPH masih belum lengkap; audit kecil yang terperinci **bukan** pengesahan keseluruhan korpus.
- 34 pasangan pengembangan Tahun 4 masih memerlukan pengesahan kesesuaian aktiviti/soalan Buku Teks pada aras item. Buku Teks Tahun 4 SK asal 306MB melebihi had muat turun connector 256MB.
- Kalender/cuti negeri A/B 2027 & penjajaran RPT belum selesai diuji.
- Telegram–Web **staging sebenar** belum dipasang dan diuji terhadap DB kanonik. Ujian local tidak boleh dilapor sebagai E2E live.
- Library kuota storan masih tidak mencukupi untuk fail ZIP besar; fail CSV bukti v50 disimpan dalam `/CikguLaju/Matematik_2027_STAGING/`. ZIP v50 boleh dimuat turun daripada perbualan.

**Release gate:** `TECHNICAL_QA=PASS`; `SUBJECT_MISALIGNMENT_CORRECTED=3 RPH`; `NUMERIC_ERROR_CORRECTED=1 RPH`; `ACADEMIC_FULL_SIGNOFF=NO`; `FINAL_READY=false`; `PRODUCTION_CHANGED=false`. **JANGAN MERGE / DEPLOY** sehingga bukti akademik dan E2E sebenar lengkap.
