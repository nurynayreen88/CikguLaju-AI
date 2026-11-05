# CikguLaju Matematik Tahun 2–6 — v32 content remediation (5 November 2026)

**KEPUTUSAN: 585/585 LULUS QA TEKNIKAL. BUKAN FINAL READY AKADEMIK ATAU TELEGRAM.**

## Kerja sebenar yang telah siap
- Sambung terus pakej calon v31, **189 RPH calon** telah dikemas kini berdasarkan **92 pasangan Tahun–SP** bagi menghapuskan pengulangan set lengkap aktiviti 1, aktiviti 2 dan PBD. Selaraskan contoh dan pengiraan dengan skop kod SP asal, termasuk pengukuhan/analisis kesilapan berasingan untuk Lesson yang berkongsi SP.
- **396/585 fail calon lain kekal** byte-for-byte daripada v31. Tahun 4 v30 tidak ditimpa.
- Ujian DOCX→PDF selepas pemurnian: **585/585 satu halaman A4**. Tiada halaman tambahan, bahagian wajib hilang, ID Tahun/Lesson salah, kawasan teks melimpah ke luar halaman, atau fon kurang 6.8 pt dalam pemeriksaan automatik. Tujuh halaman sampel dipapar untuk semakan visual.
- Pemeriksaan tiga komponen **Aktiviti 1 + Aktiviti 2 + Pentaksiran sama sepenuhnya**: v31 = 146 pengulangan melebihi entri pertama; v32 = **0**.
- Semakan ekspresi aritmetik mudah: 93 padanan lengkap disahkan menggunakan pemeriksa konservatif. Tiga calon yang kelihatan salah dalam imbasan awal sebenarnya **padanan sebahagian** daripada ungkapan pecahan/kurungan lebih panjang; jangan tafsir sebagai 3 kesilapan terbukti.
- Kod SP dalam Buku Teks wujud untuk 585 Lesson sebagaimana rekod audit v31; kewujudan ini **bukan** pengesahan aktiviti tertentu pada halaman buku.

## Penemuan baharu yang masih menghalang FINAL READY
- Memeriksa tiga bahagian sekaligus sahaja tidak cukup: masih terdapat pengulangan *satu bahagian* antara SP berbeza dalam **396 fail lain yang tidak dimurnikan**. Pemeriksaan seluruh 585 menunjukkan:
  - Aktiviti 1 sahaja: 181 kemunculan tambahan dalam 50 kelompok;
  - Aktiviti 2 sahaja: 72 kemunculan tambahan dalam 64 kelompok;
  - Pentaksiran sahaja: 203 kemunculan tambahan dalam 72 kelompok.
  Kejadian sama bukan automatik kesilapan, tetapi kelompok merentas SP mesti disemak dan diperkemas jika kaedah/tugasan tidak selari.
- Banyak calon masih mempunyai rujukan halaman buku teks/buku aktiviti **belum disahkan**; tidak boleh menggantikan halaman buku dengan nombor SP atau halaman rawak.
- Padanan isi asal 83 RPH Tahun 4 ke 117 Lesson cadangan masih belum mendapat kelulusan individu berdasarkan sumber v15; 34 sesi tambahan memerlukan justifikasi dan penilaian.
- Semakan akademik individu 585 RPH terhadap aktiviti sumber Buku Teks/Buku Aktiviti dan DSKP belum lengkap. Tiada pengesahan guru individu.
- GitHub **main** setakat audit hanya menghantar **RPT Matematik v28 DRAF/SEMENTARA** melalui callback `rpt2027_math_pdf_`; pakej RPH v32 **belum dipautkan ke enjin runtime atau DB**, belum diuji di Telegram.
- CikguLaju Render production auto-deploy `main`; jangan merge tanpa regresi, backup DB dan QA lengkap.

## Kawalan keutuhan
Pakej tempatan: `CIKGULAJU_MATEMATIK_v32_585_RPH_CONTENT_REVIEW_STAGING.zip`
- SHA-256: `f8a8cc2f4a25a8e46dde8e4f9776c7c2ec81b0c72692dc8aefecfbe0b9fa9fa6`
- 585 Word, 585 PDF individu, 585 Markdown + 5 PDF gabungan.
- Semua perubahan hanya dalam pakej local staging; **tiada** kemas kini `main`, database, Telegram, Web atau Render.

## Definisi sebelum boleh ditandakan FINAL READY
1. Setiap Lesson disahkan aktiviti/PBD, buku teks dan buku aktiviti dengan bukti halaman, bukan kewujudan kod sahaja.
2. Semua kelompok pengulangan berisiko SP berbeza dinilai.
3. 83→117 Tahun 4 diluluskan sebagai perpecahan aktiviti yang benar-benar sesuai.
4. RPT dan RPH selaras tarikh sekolah/cuti negeri serta perancangan PdP sebenar.
5. Uji RPH 585 sampel pada staging melalui enjin runtime, fail Word/PDF, kawalan akses/kuota dan regression all subjects. Hanya kemudian boleh dipertimbangkan untuk merge/penerbitan.

**Gate: FINAL_READY=false.**

Dokumentasi terdahulu: [v31 QA](./matematik_v31_585_rph_evidence_and_quality_gate_20261105.md), [v30](./matematik_t2_t6_585_rph_v30_technical_qa_20261105.md), [RPT Matematik main](https://github.com/nurynayreen88/CikguLaju-AI/tree/main/rpt_2027/matematik).
