# Audit Bahasa Arab Tahun 2–6 — sambungan 5 Nov 2026

**Status:** STAGING / DRAF / BELUM READY. Tiada perubahan `main`, `app.py`, DB produksi, Supabase pengguna, Telegram LIVE atau Web LIVE.

## Semakan dan penghasilan
- **60/60 RPH DRAF**: PdP 001–012 bagi setiap Tahun 2–6, dengan Set induksi, Aktiviti 1/2, BBM, PBD dan penutup; bukan hasil render A4.
- **20 unit** diindeks: empat unit setiap tahun. Tahun 3 Unit 4 menggunakan **الزمان** berdasarkan RPT 2026.
- **60/60 crosswalk PdP** dengan SK/SP cadangan, dipisahkan daripada urutan 20 unit, semuanya halaman buku belum disahkan.
- **15 bank aktiviti Unit 2–4**, setiap unit mempunyai kosa kata, permainan/BBM khusus dan cadangan PBD; bukan RPH siap.
- CI lama 30 RPH / 15 bank lulus pada run 42048090396. CI baharu untuk **60 RPH** perlu dibaca selepas push ini; jangan menyamakan ini dengan kelulusan pedagogi.

## Sumber yang digunakan
- DSKP Tahun 2–5 PDF Drive; DSKP Tahun 6 rujukan KSSR Semakan awam serta dokumen di portal panitia.
- RPT Kumpulan B 2026 Tahun 2–6 yang ada dalam manifest. Ini peta **PdP**, bukan jadual minggu 2027.
- Buku teks T4/T5: pemetaan julat halaman mengikut unit; buku T2, T3, T6 masih memerlukan pengesahan halaman PdP spesifik.
- Tahun 2: unit perkenalan (contoh اسم، أنا، أنت، معلم، تلميذ).
- Tahun 3: bilik darjah (contoh كرسي، سبورة، مكتب، نافذة).
- Tahun 4: bulan Masihi (contoh يناير، فبراير، مارس dan soalan ما هذا الشهر؟).
- Tahun 5: dapur dan tindakan (contoh صحن، ثلاجة، ماذا تفعل؟).
- Tahun 6: kebersihan (contoh صابون، فرشاة الأسنان، كيف تنظف؟).
- Bahasa dan aktiviti yang dirancang **tidak** menuntut padanan buku halaman tertentu sehingga penyemak membuktikan perkara itu.

## Pintu kawalan sebelum FINAL READY
1. Banding DSKP dan buku teks bagi **setiap** RPH serta wujudkan bukti halaman buku dan kod SK/SP.
2. Lengkapkan PdP keseluruhan mengikut unit dan RPT 2027 Kumpulan A/B serta kalendar negeri; jangan gunakan minggu sebagai identiti.
3. Uji Word A4 satu halaman, PDF dan susun atur Arab RTL/harakat.
4. Semak arahan guru, BBM, peranan murid, PBD dan kesahihan perkataan/ayat; semakan manual individu.
5. Audit DB v26.00 dan backup, uji penghantaran Telegram/Web dari penjana dan sumber sama.
6. Kekalkan semua status DRAF sehingga kelulusan manual individu. **READY = 0**.

Status berangka ini mengira fail yang wujud, **bukan** 60 RPH yang telah disahkan.

## 5 Nov 2026: BUKU TEKS TAHUN 6 — BUKTI HALAMAN
- Pengenalan bibliografi diperiksa melalui HTML buku sumber: DBP untuk KPM, cetakan pertama 2021, ISBN 978-983-49-3300-5.
- TOC Tahun 6 Unit 1–4 = **1–30, 31–60, 61–90, 91–120** (halaman bercetak). Direkod dalam CSV unit; **jangan samakan julat unit dengan pengesahan halaman RPH**.
- Buku mengandungi contoh kod SP di tepi aktiviti dan latihan mendengar/menulis/bertutur; 12 cadangan padanan PdP Unit 1 kini di fail `audits/bahasa_arab_y6_textbook_page_evidence_20261105.json`.
- **Bendera konflik**: Tahun 6 PdP 004 menggunakan SP 2.1.1 sedangkan contoh halaman buku 2 menampilkan 2.1.2/2.1.4. Perlu adjudikasi, jangan ubah SP automatik.
- Sumber HTML BT: https://anyflip.com/gcmci/mxcs/basic. DSKP Tahun 6: https://anyflip.com/mhtcw/pstm/basic. Dokumen indeks sumber Drive: https://docs.google.com/document/d/1z5rz0j-xtIwm1JF8-p0sc5BQvk8q_W_UOZR3yFAnl7A/edit?usp=drivesdk.
- **0 RPH READY**, kerana padanan 1:1 PdP/halaman dan ujian Word/PDF RTL belum dibuat.

### Pembetulan Tahun 6 PdP 004
**2.1.1 → 2.1.2** dan aktiviti/kosa kata diselaraskan dengan Buku Teks Tahun 6 Unit 1 halaman bercetak 2. DSKP SP 2.1.2 ialah membaca kata berhuruf seakan sama. Status kekal DRAF/BELUM READY sehingga semakan individu dan render Word/PDF.

### Padanan edisi Buku Teks (front matter PDF Drive + teks BT Year 6)
- T4: **DBP/KPM, Cetakan Pertama 2019**, ISBN **978-983-49-2480-5** daripada PDF Drive asal.
- T5: **DBP/KPM, Cetakan Pertama 2020**, ISBN **978-983-49-2838-4** daripada PDF Drive asal.
- T6: **DBP/KPM, Cetakan Pertama 2021**, ISBN **978-983-49-3300-5** daripada HTML buku teks.
- Tahun 2/3 ISBN **belum disahkan**. Semua RPH kekal DRAF, 0 READY. Fail asal dalam Drive tidak diubah.

## Pembetulan penting tajuk Tahun 3 Unit 4 (6 Nov 2026)
Semakan teks isi kandungan buku sebenar DBP/KPM Tahun 3, cetakan pertama 2018, ISBN 978-983-49-2033-3, membuktikan tajuk unit sebenar ialah **الوقت كالذهب**, julat halaman bercetak 87–117. Label **الزمان** ialah tema masa yang dibincangkan dalam unit, **bukan** nama rasmi unit. Sebarang catatan terdahulu bahawa `الزمان` tajuk unit adalah *dibatalkan/superseded* tanpa memadam sejarah audit.

Buku Teks Tahun 3 unit 1–4: 1–28, 29–58, 59–86, 87–117. Tahun 2 Buku Teks ISBN **978-983-49-1589-6**, Buku Aktiviti ISBN **978-983-49-1590-2**, diterbitkan DBP November 2017 menurut katalog penerbit. **Tiada bukti halaman individu Tahun 2 ditambah.** Semua status kekal DRAF, 0 READY.

Sumber: https://www.scribd.com/document/438677752/Bahasa-Arab-Tahun-3-Teks-KSSR-Semakan ; https://jendeladbp.my/ujana/bahasa-arab-tahun-3-bt-pt/ ; https://stage.jendeladbp.my/ujana/bahasa-arab-tahun-2-bt-pt/ ; https://jendeladbp.my/ujana/bahasa-arab-tahun-2-ba-pt/

## 6 Nov 2026 — Tahun 4 Unit 1, enam PdP pertama
Enam draf RPH Tahun 4 PdP 001–006 dikemaskini dengan bukti contoh muka surat BT DBP/KPM 2019: 2, 2, 4–5, 3, 7, 3. Aktiviti diperincikan menggunakan contoh asli kata ال, bulan Masihi dan tulisan. Rujukan fail: `audits/bahasa_arab_y4_textbook_pdp001_006_evidence_20261106.json` dan https://anyflip.com/rzqgi/ejrv/basic. Semua kekal DRAF, belum lulus pengesahan RPT 2027 atau fail A4 Word/PDF.

## Pembetulan Tahun 5 Unit 3 — 6 Nov 2026
Tajuk Buku Teks Tahun 5 Unit 3 ialah **هيا نشترك في الأنشطة اللاصفية** (Aktiviti Kokurikulum / Luar Bilik Darjah), bukan **هيا نشترك في الأنشطة الصفية**. Bank aktiviti kini menggunakan contoh kelab/persatuan/unit beruniform. Disahkan silang menggunakan bahan PdP sekolah yang menyebut buku teks halaman 65 dan RPT 2024/25. Buku Teks Tahun 5 DBP/KPM 2020 masih sumber asas; halaman individu PdP untuk unit ini belum diluluskan. Indeks CSV, manifest, bibliografi dan bank aktiviti diseragamkan tanpa menukar status READY.

## Semakan sumber 6 November 2026 — Tahun 5 PdP 001–012
Buku teks DBP/KPM cetakan pertama 2020 ISBN 978-983-49-2838-4 dan DSKP asal dalam Drive telah dipadankan pada aras teks untuk 12 RPH draf Unit 1 `في المطبخ`. Setiap RPH mendapat rujukan halaman bercetak: **2, 2, 4+6, 3, 7–9, 10, 13–14, 15, 15, 14–15, 16, 19–20**. PBD dan tindakan guru-murid dikekalkan. Dialog serta tulisan PdP 007–011 diselaraskan dengan aktiviti buku.

**Bendera belum selesai:** (1) PdP 002 kod 1.1.2 DSKP tiada pada latihan buku h.2; (2) PdP 004 buku h.3 berfokus huruf ب/ن sedangkan draf berfokus bunyi ث/س/ص; (3) PdP 012 contoh p19 berbeza daripada SP 1.4.1 yang tercetak di p20. Perlu pengesahan SK/SP dan pemetaan RPT individu, tidak boleh auto-READY.

Fail bukti `audits/bahasa_arab_y5_pdp001_012_source_audit_20261106.json` menyimpan kod buku dan had pengesahan; pembetulan tidak menukar status **0 FINAL READY**. Word/PDF RTL A4 belum diuji.

## 6 November 2026 — Tahun 4 PdP 007–012
Enam draf tambahan disemak berdasarkan Buku Teks Tahun 4 DBP/KPM 2019 (halaman 10, 15, 25, 15, 16, 20). PdP 007 menulis nama bulan; PdP 008/010 menggunakan dialog hari jadi; PdP 009 intonasi; PdP 011 ucapan hari jadi. **Bendera PdP 012:** buku halaman 20 mengandungi kod SP 1.4.1 untuk dialog berkait, tetapi contoh ayat draf tentang Hari Guru belum sepadan teks buku; jangan tanda READY tanpa adjudikasi.

Fail: `audits/bahasa_arab_y4_pdp007_012_source_audit_20261106.json`. Kini 12/12 draf Unit 1 Tahun 4 mempunyai sumber halaman bercetak pada aras teks, tetapi tiada kelulusan individu akhir atau Word/PDF RTL. **0 FINAL READY**.

## 6 Nov 2026 — Remediasi empat RPH berpandukan buku teks
- Y5 PdP 002: SP ditukar **1.1.2 → 1.1.3**, dan aktiviti bertumpu membezakan bunyi seakan sama sebagaimana DSKP dan BT halaman 2.
- Y5 PdP 004: contoh h.3 dipilih semula (ثلاجة، سكين، صحن); kad tambahan سمكة diberi label pengayaan guru. SP 2.1.1 dikekalkan.
- Y5 PdP 012: draf lama berasaskan contoh p19 diganti dialog ibu-anak tentang memasak yang sepadan dengan latihan berkod 1.4.1 pada h.20.
- Y4 PdP 012: contoh draf Hari Guru diganti dialog Hari Bahasa Arab pada BT Tahun 4 h.20 (1.4.1).
- Rekod konflik sumber dikemas kini sebagai dibetulkan pada kandungan, **bukan kelulusan FINAL READY**; turutan 2027 RPT, pemeriksaan halaman imej, Word/PDF RTL dan semakan guru belum selesai.

## Tahun 3 PdP 001–012: audit sumber buku teks (6 Nov 2026)
Semua 12 draf Tahun 3 Unit 1 menerima catatan halaman bercetak Buku Teks DBP/KPM 2018 dan kod SP mengikut aktiviti yang ditemui: 2+6, 2+6, 2+6, 2+6, 4+8, 5+9, 5+9, 11–12, 11–12, 13–14, 20+24, 16–17. Draf PdP 004, 008–012 dimurnikan supaya kosa kata/objektif mengikuti buku teks. Frasa tambahan guru ditandakan berasingan. Pautan bukti https://www.scribd.com/document/438677752/Bahasa-Arab-Tahun-3-Teks-KSSR-Semakan dan fail `audits/bahasa_arab_y3_pdp001_012_source_audit_20261106.json`. **Status masih DRAF, 0 READY**, belum semak keseluruhan RPT 2027 dan approval guru.

## Tahun 6 PdP 001–012: semakan teks buku asal (6 Nov 2026)
12 draf awal kini menerima catatan bukti halaman bercetak bagi buku DBP/KPM cetakan pertama 2021: 2,3,4–5,2,6–9,10–12,13–14,14–15,13–15,14–15,16,18. PdP 012 diubah daripada contoh sabun kepada contoh baldi (h18) untuk kod 1.4.1; tambahan ayat guru ditandakan. PdP 009 membezakan larangan pembaziran air sebagai pengayaan di luar contoh h13–15. Bukti disimpan dalam `audits/bahasa_arab_y6_pdp001_012_text_source_audit_20261106.json`. Status semua kekal DRAF; buku PDF imej asal dan RPT 2027 belum diluluskan individu.

## Tahun 2 PdP 001–012 — Buku Teks DBP 2017 dijumpai (6 Nov 2026)
- Buku Teks asal Bahasa Arab Tahun 2 KSSR Semakan 2017 DBP, ISBN **978-983-49-1589-6**, teks digital boleh dibaca di https://anyflip.com/slrpb/qzcr/basic dan portal sekolah https://sites.google.com/moe-dl.edu.my/fcpi/bahasa-arab/tahun-2-bahasa-arab/%D8%A7%D9%84%D9%88%D8%AD%D8%AF%D8%A9-%D8%A7%D9%84%D8%A3%D9%88%D9%84%D9%89-1.
- 12 draf RPH Tahun 2 Unit 1 kini ada rujukan halaman bercetak secara spesifik: **2+4; 2+4; 3+5; 2+4; 3+5; 6; 6; 8; 8; 9–11; 17; 12–14**. Pemetaan SK/SP dibanding dengan PDF DSKP Tahun 2 yang mengekalkan identifier Arab dengan betul: https://cdn1.get-qr.com/files/67c8ee65569c40f8cc02dedb/1741221735772-edfd2d1acbd2cca80728a1fbd9edcc66.pdf.
- **Empat bendera OCR kod buku** PdP 002,004,010,011. Pemadanan kemahiran didapati relevan dan SP DSKP sah, tetapi jangan dakwa cetakan SP dalam buku telah diluluskan sehingga semak halaman imej asal.
- Fail bukti `audits/bahasa_arab_y2_pdp001_012_text_source_audit_20261106.json`. Sekarang **60/60 draf awal mendapat semakan teks sumber**; ini TIDAK bermakna tahun lengkap / siap diterbitkan. **0 FINAL READY** dan 15 unit Unit2–4 belum RPH.

## Tahun 4 Unit 2: 12 RPH individu tambahan (6 Nov 2026)
- `rph_standalone/bahasa_arab/year4/lesson_013.md` hingga `lesson_024.md` disediakan berdasarkan latihan Buku Teks asal DBP 2019, Unit 2 **من في المدرسة؟** halaman bercetak 30,30,31,31,32,32,34,36,38,42,44,48 dan kod SP pada setiap latihan.
- Setiap RPH mempunyai set induksi, aktiviti utama (tindakan guru+murid), BBM, PBD, penutup, refleksi dan sumber. Fail peta cadangan `rpt_2027/bahasa_arab/year4_unit2_pdp013_024_DRAF.csv`; bukti `audits/bahasa_arab_y4_unit2_pdp013_024_text_source_audit_20261106.json`.
- **Penjadualan 013–024 ialah cadangan**, bukan jumlah PdP Unit 2 rasmi. Halaman 49–56 masih belum dipetakan. Keseluruhan kini **72 RPH draf**, 15 bank unit dan **0 FINAL READY**.

## 6 Nov 2026 — Tahun 4 Unit 2 sambungan, Unit 3 awal
- 4 RPH cadangan PdP025–028 Unit2 menggunakan latihan Buku Teks asal h49 (dialog), h53 (permainan susun ayat), h54 (persembahan lisan), h56 (diorama). Jumlah Unit2 kini 16 draf yang merujuk halaman tersebar 30–56; **tidak bermaksud unit diluluskan RPT 2027**.
- 14 RPH cadangan PdP029–042 Unit3 **أحب مدرستي** bersumber latihan h58,59,60,62,64,66,70,72,76,82,84. Kemahiran dengar/baca/tulis, kedudukan sekolah dan projek. Projek ialah aktiviti murid, bukan salinan buku.
- Fail peta `rpt_2027/bahasa_arab/year4_unit2_tail_unit3_pdp025_042_DRAF.csv` dan audit `audits/bahasa_arab_y4_unit2_tail_unit3_pdp025_042_text_source_audit_20261106.json`. **90 RPH draf** Tahun2–6, tiada FINAL READY. Langkah 2027 A/B, semakan visual dan kelulusan guru masih belum dibuat.

## 6 November 2026 — QA A4 untuk 90 RPH lulus
Run GitHub Actions `42124849955` (head ade2e7f465a6f49a473e53923f7387d6d2dce596) menyiapkan penjanaan **90 DOCX + 90 PDF** dan mengesahkan setiap PDF satu halaman A4, Amiri/Arabic RTL; pratonton disimpan sebagai artifak workflow. Ini **lulus teknikal sahaja**: tiada proofread setiap halaman, pengesahan SK/SP per halaman visual, jadual RPT 2027 A/B atau manual pedagogi. Kekalkan **0 FINAL READY** dan tiada deploy. Pautan https://github.com/nurynayreen88/CikguLaju-AI/actions/runs/42124849955.

## 6 November 2026 — Tahun 4 Unit 4 (16 RPH baharu)
Unit **بيتي جنتي** kini mempunyai 16 RPH individu cadangan PdP043–058. Sumber: Buku Teks DBP/KPM Tahun 4 cetakan 2019 h86,87,88–89,90,91,93,94,97,98,99,100,104,105,108,112 serta kod SP yang muncul pada latihan bertema rumah. Aktiviti ditulis berbeza mengikut kemahiran fonetik, kosa kata, soalan tempat, dialog, tulisan, lawatan warga emas dan projek siluet. Setiap RPH mempunyai pengajaran guru/murid, PBD dan refleksi. 
Peta `rpt_2027/bahasa_arab/year4_unit4_pdp043_058_DRAF.csv` dan fail bukti `audits/bahasa_arab_y4_unit4_pdp043_058_text_source_audit_20261106.json`.
**Jumlah 106 RPH DRAF**, 58 Tahun 4 meliputi 4 unit secara **calon**, bukan RPT 2027 rasmi atau kelulusan individu. QA A4 terkini disahkan 90; jalankan 106 selepas commit. **0 FINAL READY**, jangan deploy.

## 6 Nov 2026 — Ujian A4 untuk 106 RPH draf LULUS
GitHub run `42127983356` menghasilkan 106 Word dan 106 PDF A4 Arab (font Amiri), dengan semakan automatik setiap PDF tepat satu halaman; artifak pratonton disimpan. Pautan: https://github.com/nurynayreen88/CikguLaju-AI/actions/runs/42127983356. Ini hanya **lulus teknikal** dan tidak membuktikan susunan PdP dalam RPT 2027, mutu bahasa/sumber halaman secara visual atau kelulusan guru. **0 FINAL READY**.

## 6 November 2026 — Tahun 5 Unit 2 (16 RPH baharu)
Unit **ما ألذ الطعام!** Buku Teks Tahun5 DBP/KPM cetakan 2020 (ISBN 978-983-49-2838-4) dan DSKP Tahun5 dibaca untuk latihan halaman bercetak **30,30,31,31,32,32,34,35,36,37,38,41,42,44,47,56**. Ditambah 16 RPH draf individu PdP013–028: fonetik ح/خ dan ذ/ز; dengar makanan; klasifikasi; projek audio; bacaan minuman; menulis kata; dialog jual beli; ayat buah segar; projek kolaj.
Peta draf `rpt_2027/bahasa_arab/year5_unit2_pdp013_028_DRAF.csv`; audit `audits/bahasa_arab_y5_unit2_pdp013_028_text_source_audit_20261106.json`. Nombor PdP calon tidak sama dengan pengesahan RPT 2027; visual halaman dan kelulusan individu tiada. Jumlah **122 draf**, **0 FINAL READY**. QA Word/PDF untuk 122 masih perlu lulus.

## 6 Nov 2026 — 122 Word/PDF A4 berjaya
GitHub Actions `42131146183` pada commit `41a0265769c7035cfe613e380c4dc6d2baeac980` berjaya untuk 122 DOCX + 122 PDF, setiap PDF satu halaman A4 dan artifak pratonton tersedia. Pautan https://github.com/nurynayreen88/CikguLaju-AI/actions/runs/42131146183. CI pertama struktur pada head ini gagal kerana status terakhir mencatat lulus 106, bukan 122. Rekod telah diselaraskan supaya set 122 diuji tanpa menukar status kelulusan pedagogi. **0 FINAL READY**.

## 6 Nov 2026 — Tahun5 Unit3: 16 RPH draf kokurikulum
Buku Teks Tahun5 DBP/KPM 2020, Unit3 **هيا نشترك في الأنشطة اللاصفية** (aktiviti kokurikulum), halaman 58,58,59,59,60,60,62,63,64,66,69,70,72,75,77,84. 16 RPH baru PdP029–044 berkaitan fonetik ت/ط dan ق/ك, acara sukan, kelab/persatuan/unit beruniform, dialog penyertaan, menulis ayat berkait dan projek Tarsia. Rujukan SP mengikuti kod yang dicetak dalam latihan asal; nombor PdP calon dan perlu pengesahan RPT 2027.
Peta `rpt_2027/bahasa_arab/year5_unit3_pdp029_044_DRAF.csv`; bukti `audits/bahasa_arab_y5_unit3_pdp029_044_text_source_audit_20261106.json`. Keseluruhan **138 RPH DRAF**, **0 READY**, Unit4 Tahun5 masih belum dibina. QA Word/PDF 138 belum disahkan.

## 6 Nov 2026 — 138 Word/PDF lulus A4
GitHub Actions run `42132565716` (https://github.com/nurynayreen88/CikguLaju-AI/actions/runs/42132565716) lulus untuk **138 Word dan 138 PDF**, setiap PDF satu halaman A4, format Arab Amiri dan artifak pratonton tersedia. Ujian struktur pertama pada commit sebelumnya gagal kerana pemeriksaan status teknikal lama, bukan kesilapan isi RPH; metadata dan ujian dikemas kini tanpa mengubah status 0 READY. 
