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
