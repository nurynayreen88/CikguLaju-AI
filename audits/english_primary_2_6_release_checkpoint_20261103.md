# Audit English Tahun 2–6 — checkpoint pembetulan sumber 3 November 2026

## Disahkan melalui lima SOW rasmi KPM dan RPT 2027 induk

- 800/800 fail Lesson `lesson_001.md`–`lesson_160.md` bagi Tahun 2, 3, 4, 5 dan 6 wujud.
- Indeks SOW tahun 2–6 berjumlah 800 Lesson. Semua pasangan 766 pasangan LS cetakan SOW + 1 pasangan LS yang disahkan daripada DSKP **sepadan** dengan header RPH (160 + 160 + 150 + 151 + 146).
- 33/800 Lesson rasmi menyerahkan standard tertentu kepada guru (Y4=10, Y5=9, Y6=14); jangan cipta kod rasmi.
- SOW Tahun 3 Lesson 61 mencetak Complementary Reading CS 3.3 dan LS terpotong 3.1. Dokumen DSKP KPM Tahun 3 SK (2018, p.31) dan DPK KPM 2.0 menyenaraikan Reading 3.3.1; RPH serta RPT sedia ada sudah tepat. Indeks kini menggunakan 3.3.1 berdasarkan DSKP, sambil mengekalkan rekod ralat cetakan SOW.
- **RPT induk 2027:** 800/800 Lesson hadir, 766 pasangan kod sama seperti cetakan SOW dan 1 pasangan tambahan disahkan melalui DSKP, dan 800/800 label focus sepadan. Tiada percanggahan hard-code; cetakan Y3 L61 ditandakan resolved melalui DSKP (bukan pembetulan pada PDF SOW).
- Pengecualian TOPIC: SOW Tahun 3 Lesson 20 mencetak "Welcome" walaupun aktiviti mengajar daily routines, unit sekeliling "Every day"; RPT dan RPH dikekalkan "Every day".

## Pembetulan spesifik dikomit melalui PR #159

- Y5 L141: kod Writing **4.2.4** menurut jadual Lesson SOW, aktiviti Gulliver's Travels (dua gambar, There is/There are) dan PBD khusus; percanggahan kod **4.2.2** dalam Appendix SOW masih direkod. Adapter Year5 kekal opt-in/disabled in production.
- Y6 L15 dan L21: poem *The Sandwich* by Tony Bradman, Anthology pp.28–29; RPH dan renderer overlay menggunakan Silly Sandwich 10-ingredient spelling serta Flow Map+punctuation.
- Y6 L25: projek *Classroom of the Future* (non-textbook Speaking) dengan poster, peranan dan pembentangan.
- Y6 L26 dan L31: *Toes* by Judith Nicholls p30 (nota kaki/puisi badan).
- Y6 L37: *Akbar's Dream*, guidebook pp35–36, ramalan berpandukan ilustrasi dan naratif.
- Y4 L30: SOW rasmi menyatakan **CD2 Track 29**, bukan CD1 Track 29; rujukan RPH dibetulkan, ujian regresi diwujudkan. MP3 sebenar belum dimainkan.
- Y2 L160: SOW memang menyatakan Language Arts 42; tidak diubah.

## RPT 2027 yang sudah diselaraskan

Google Sheet `CIKGULAJU ENGLISH Y2-Y6 RPT RPH ALIGNMENT 2027 — STAGING 20261101`, tab `MASTER ENGLISH 800 LESSON 2027`:
- Y6 F656/F662: *The Sandwich* pp28–29.
- Y6 F657: Unit 1 Workbook Check-up pp16–17 & TB p37.
- Y6 F666: future-classroom non-textbook materials.
- Y6 F667/F672: *Toes* p30.
- Y6 F678: *Akbar's Dream* teacher guide pp35–36.

**Penting:** Fail PDF RPT 2027 Tahun 6 terdahulu dalam repository/Drive adalah versi sebelum pembetulan Sheets dan **perlu dijana semula**. Jangan label PDF itu FINAL VERIFIED.

## Batasan READY

Ini ialah audit nombor Lesson, standard, dan pembetulan kandungan terpilih. Masih belum lengkap audit setiap halaman Student/Pupil Book, Teacher's Book, Workbook, kelulusan bahan non-textbook, fail audio sebenar + playback dan pautan Telegram, eksport Word/PDF A4 serta kelulusan guru bagi semua 800 Lesson. Semua RPH tanpa bukti per-Lesson tidak boleh dilabel READY. Tahun 5 adapter masih dimatikan secara lalai untuk menjaga pengguna.

Tidak ada reset DB, migrasi pengguna, pengurangan/penambahan kuota atau gantian data lama melalui PR ini.
