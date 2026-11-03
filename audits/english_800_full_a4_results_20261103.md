# English Tahun 2–6 — laporan penuh susun atur Word A4, 3 November 2026

## Method

CI menjana **800 fail DOCX daripada 800 sumber RPH** menggunakan salinan fungsi Word semasa `app.py` yang dibandingkan melalui AST dengan fungsi aktif. LibreOffice menukar Word kepada PDF; jumlah halaman dan saiz A4 diukur untuk setiap Lesson. Tahun 6 menggunakan pemadat Word 8pt yang sudah tersedia dalam production.

Ini **bukan** penjana PDF ReportLab asal atau ujian dokumen dihantar kepada pengguna Telegram. Pemeriksaan buku teks, audio, kelulusan pentaksiran/aktiviti oleh guru, dan visual menyeluruh masih berasingan.

## First pass — [GitHub Actions #41644237841](https://github.com/nurynayreen88/CikguLaju-AI/actions/runs/41644237841)

| Tahun | Word dibuat | PDF dibuat | Satu halaman A4 | Punca pengecualian |
|---|---:|---:|---:|---|
| 2 | 160 | 160 | 155 | L2, L3, L12, L13, L14 dua halaman |
| 3 | 160 | 160 | 160 | Tiada |
| 4 | 160 | 160 | 160 | Tiada |
| 5 DRAF | 151 | 151 | 148 | L90, L110, L136 dua halaman; 9 Lesson pilihan guru tidak menggunakan adapter fixed-code |
| 6 | 160 | 160 | 160 | Tiada |

## Second pass — [GitHub Actions #41644999160](https://github.com/nurynayreen88/CikguLaju-AI/actions/runs/41644999160)

| Tahun | Word | PDF | Satu halaman A4 | Catatan |
|---|---:|---:|---:|---|
| 2 | 160 | 160 | **160** | Pemadatan 8pt **hanya** L2,3,12,13,14 (ujian staging; belum live) |
| 3 | 160 | 160 | **160** | Kod semasa |
| 4 | 160 | 160 | **160** | Kod semasa |
| 5 DRAF | 160 | 160 | **160** | Pemadatan staging L90,110,136; 9 Lesson pilihan guru sebagai pratonton *teacher-selected*, **bukan** release/CS-LS rasmi |
| 6 | 160 | 160 | **160** | Pemadat 8pt yang sudah live |
| **Jumlah** | **800** | **800** | **800** | Lulus susun atur di mesin CI; bukan READY keseluruhan |

**Pengesahan tekstual:** Semua kompak yang dilaksanakan dalam second pass membandingkan kandungan Word sebelum/selepas dan menggagalkan ujian sekiranya teks berubah. PDF conversion berjaya dan tiada Lesson mempunyai nisbah teks diekstrak yang ditandakan suspek menurut ambang diagnostik 60%; ini bukan pengganti pemeriksaan visual setiap halaman.

**Kesimpulan tindakan:** Pasang pemadat terhad untuk lima Word RPH Tahun 2 hanya selepas CI regresi wrapper lulus. Tahun 5 kekal DRAF dan production runtime OFF, termasuk sembilan lesson pilihan guru yang memerlukan guru memilih/mengesahkan standard. Jangan reset DB atau ubah langganan, audio, menu subjek, atau sumber asal.

JSON terperinci 160 Lesson/tahun ialah artifak CI bernama `full-English-A4-Y2` hingga `full-English-A4-Y6`; artifak mempunyai tempoh simpanan 7 hari.
