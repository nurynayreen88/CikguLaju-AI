# Agihan Matematik SK Tahun 2–6 sebelum UASA

Semakan pada 17 November 2026 meliputi 585 Lesson. Setiap tahun mempunyai 117 Lesson dengan urutan, kod SK dan kod SP yang sama dalam RPT Web, PDF Telegram v28 dan bank RPH v60. Agihan RPT produksi dan indeks RPH Pantas sepadan. Setiap tahun ada 15 Lesson selepas Minggu 39. Kesemua fasa RPH v60 berjumlah 60 minit bagi setiap Lesson. Sumber ialah [RPT Web dan indeks produksi](https://github.com/nurynayreen88/CikguLaju-AI/tree/57aa5be4c9c0cc8511a545ee88dfb4423df50cb9), [RPT Telegram v28](../rpt_2027/matematik) dan [bank RPH v60](../rph_standalone/matematik/README_v60_MAIN_SOURCE.md).

## Draf takwim 96 jam

[Agihan draf](../staging/matematik/rpt_2027_agihan.json) memberikan setiap tahun 75 Lesson × 60 minit dan 42 Lesson × 30 minit, dengan semua 117 nombor asal dan tarikh Kumpulan A/B. Daripada 35 minggu dengan PdP baharu, 19 minggu mempunyai empat Lesson, sembilan mempunyai tiga Lesson dan tujuh minggu pendek mempunyai dua Lesson. Minggu biasa menggunakan 150–180 minit. Minggu pendek menggunakan 120 minit. Daripada calon slot 30 minit, 164 merujuk sesi Aplikasi/PBD dalam PDF Telegram dan 46 merujuk sesi pengajaran atau penerokaan. Masing-masing masih memerlukan penyesuaian aktiviti dan semakan guru.

M06 dan M19 kosong. M18 diperuntukkan untuk pentaksiran. M39–44 tersedia untuk ulang kaji, UASA dan aktiviti sekolah. Pada M10, Kumpulan A bermula pada 15 Mac berdasarkan cuti tambahan sehari pada 14 Mac. PdP terakhir dijadualkan pada M38, 17–21 Oktober (A) dan 18–22 Oktober (B). [Kalendar Akademik KPM 2027](https://www.moe.gov.my/kalendar-akademik-semasa) · [Peruntukan minimum Matematik SK](https://www.moe.gov.my/surat-pekeliling-ikhtisas-bilangan-5-tahun-2019-pe).

## Penjajaran akademik Tahun 2 dan 3

Perbandingan awal dengan [Dokumen Penjajaran Matematik Tahap I Edisi 3, hlm. 19–35 dan 39–48](https://anyflip.com/hhixc/dztg/basic/) serta [hlm. 49–61](https://anyflip.com/hhixc/dztg/basic/51-66) menemukan 49 Lesson Tahun 2 dan 69 Lesson Tahun 3 dengan sekurang-kurangnya satu nombor SP lama yang tiada dalam Edisi 3. Daripada 118 Lesson itu, 47 ialah calon slot 30 minit. Senarai [triaj kod](../staging/matematik/penjajaran_tahap1.json) merekodkan Lesson, minggu dan kod untuk semakan. Kod yang sama boleh membawa skop baharu. Contohnya, SP 1.2.1 Tahun 3 dalam v60 ialah penulisan nombor, sementara dalam Edisi 3 kod itu merujuk anggaran. [Surat Siaran KPM Bil. 6 Tahun 2024](https://www.moe.gov.my/index.php/surat-siaran-kpm-bil-6-tahun-2024).

### Cadangan padanan bagi unit nombor bulat

| Tahun | Lesson v60 | Padanan Edisi 3 untuk semakan | Penyesuaian yang diperlukan |
| --- | --- | --- | --- |
| 2 | 001, 003, 004 | 1.1.1, hlm. 19 | Gunakan latihan membilang dan menulis angka atau perkataan dalam lingkungan 1000. Pisahkan peranan setiap Lesson supaya latihan tidak berulang. |
| 2 | 002, 006–007 | 1.2.1, hlm. 20–21 | Kekalkan fokus nilai tempat, nilai digit dan cerakinan. Perbandingan nilai dua nombor di bawah 1.1.2 memerlukan evidens tersendiri. |
| 2 | 005 | 1.1.3, hlm. 20 | Sahkan contoh turutan menaik dan menurun, serta tambah semakan individu. |
| 2 | 008–009 | 1.4.1 dan 1.5.1, hlm. 21–22 | Kekalkan set rujukan untuk anggaran. Pembundaran dalam Edisi 3 meliputi puluh dan ratus; Lesson 009 kini berfokus pada ratus. |
| 2 | 010–012 | 1.3.1 dan 1.3.2, hlm. 21 | Asingkan menyebut pola daripada melengkapkan pola. Untuk melengkapkan pola, guna sela satu, dua, lima dan sepuluh sebagaimana catatan dokumen. |
| 2 | 013–014 | 2.2.1 untuk contoh tolak, hlm. 24 | Contoh aplikasi sedia ada ialah masalah baki. Letakkan selepas pengajaran operasi tolak, atau beri tugasan baharu dalam skop nombor bulat jika slot dikekalkan. |
| 3 | 001, 003 | 1.1.1(i), hlm. 39 | Gabungkan bukti membilang dan menulis nombor dalam skop hingga 10 000. |
| 3 | 002, 006–007 | 1.1.1(ii), hlm. 40 | Gunakan aktiviti nilai digit dan cerakinan. Tambah bukti bagi membanding hingga tiga nombor untuk 1.1.2 secara berasingan. |
| 3 | 004–005 | 1.4.1 dan 1.1.2, hlm. 40–42 | Padankan sebutan pola serta melengkapkan turutan dengan objektif masing-masing. Semak pertindihan dengan Lesson 010–011. |
| 3 | 008–011 | 1.2.1, 1.3.1, 1.4.1 dan 1.4.2, hlm. 42 | Asingkan anggaran, pembundaran, sebutan pola dan melengkapkan pola. Sahkan skop sehingga enam nombor bagi tugasan pola. |
| 3 | 012–013 | 2.1.1 untuk contoh tolak, hlm. 43 | Ambil kira turutan pengajaran operasi sebelum latihan situasi harian, atau sediakan tugasan nombor bulat yang sepadan untuk slot ini. |

## Hasil ujian dan status

Semakan setempat mengesahkan kesemua 585 Lesson dan 175 jumlah minit mingguan, serta 44 baris tarikh bagi setiap tahun dalam PDF 10 halaman. Jalankan `python staging/matematik/eksport_agihan.py --output /tmp/Agihan_Matematik_SK_2027.pdf` dengan ReportLab dan DejaVu Sans untuk mengulang eksport. Status **HOLD** sehingga penjajaran Tahun 2–3, padanan bahan/aktiviti dan minit RPH disemak. Audit akademik Tahun 6 dalam [PR #460](https://github.com/nurynayreen88/CikguLaju-AI/pull/460) melibatkan sumber RPH native dan kekal sebagai semakan berasingan. Agihan ini belum diterbitkan di Web atau Telegram.
