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
