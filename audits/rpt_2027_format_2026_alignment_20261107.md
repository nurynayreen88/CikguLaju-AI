# Audit susun atur RPT 2027 CikguLaju — 7 Nov 2026

**Skop:** sekolah rendah, Tahun 2–6 (RBT/Sejarah Tahun 4–6). Tahun 1 KP2027 mesti diaudit berasingan dan tidak disalin daripada KSSR tanpa semakan.

## Punca isu

RPT Web dan Telegram menggunakan sumber PDF yang tidak sama daripada segi reka letak dan struktur. Menyamakan fail PDF dengan meletakkan logo atau muka depan sahaja tidak menyelesaikan masalah: isi jadual, bilangan lajur, tarikh A/B dan rujukan unit berbeza.

| Subjek | Sumber aktif / bukti | Jurang layout |
|---|---|---|
| English 2–6 | 5 PDF `RPT_ENGLISH_TAHUN_*_2027_UNTUK_GURU.pdf` | Rujukan reka letak (bukan bukti kelulusan semua Lesson) |
| BM 2–6 | 5 PDF `RPT_Bahasa_Melayu_Tahun_*_2027_DRAF.pdf` | Penjana semasa memaksa satu minggu satu helaian; semak halaman panjang dan padatan baris |
| Matematik 2–6 | 5 PDF `v28_SEMENTARA` | Susunan templat dan kandungan masih sementara |
| Pendidikan Islam 2–6 | 5 PDF per tahun | Pastikan aksara Jawi/Arab dan teks panjang kekal boleh dibaca |
| PJPK 2–6 | 5 PDF DRAF | Bezakan PJ/PK dan lajur tarikh/catatan |
| PSV 2–6 | 42 PdP setiap tahun dalam CSV (T6 guna nama lajur berbeza) | Penjana 4 lajur, tarikh cadangan A/B mempunyai CSV berasingan |
| Pendidikan Moral 2–6 | 96 sesi/tahun, dua CSV A/B, RPH core/pengukuhan berlainan status | Jadual/penjana PDF belum satu gaya |
| RBT 4–6 | 32 PdP/tahun, CSV + JSON RPH | Penjana 4 lajur; tarikh A/B masih kosong, jangan mereka minggu rasmi |
| Sains | Sumber RPT pembangunan, tiada set PDF penuh pada laluan `rpt_2027/sains` | **Belum boleh** diratakan sebagai final |
| Sejarah 4–6 | CSV RPT tahun 4–6, tiada 3 PDF terbit | Perlu audit DSKP/rujukan 2026 dulu |
| Bahasa Arab | CSV draf, tiada PDF terbit | Tulisan Arab perlu semakan RTL dan font |
| Pendidikan Muzik | Staging 5 RPT, audit lagu/nota dan kalendar belum final | Jangan terbitkan template seragam tanpa semak notasi |

## Keputusan reka letak baharu

1. **Kertas A4 landskap**, muka depan dengan nama sekolah, guru, kelas dan negeri.
2. **Lima lajur konsisten:** `MINGGU/TARIKH`, `UNIT/TAJUK/PdP`, `SK`, `SP`, `CATATAN/BAHAN`. Teks SK/SP penuh tidak digugurkan; hanya tajuk lajur dipendekkan supaya tidak terpotong.
3. Tarikh **Kumpulan A dan B dalam jadual yang sama** apabila sumber ada. Tarikh tidak diketahui ditulis `Belum ditentukan`. Identiti tetap rekod ialah PdP/Lesson, **bukan minggu**.
4. `Unit 1: Nama Unit` dipaparkan sekali dalam medan unit, tanpa gabungan label yang berganda.
5. Setiap PdP ditulis sebagai satu baris jadual, text wrap automatik, header berulang jika melimpah halaman; tidak memaksa satu minggu = satu halaman.
6. SK dan SP diasingkan ke kolum berlainan; aktiviti/pentaksiran dan rujukan buku dicatat mengikut sumber, **bukan ayat generik yang dicipta**.
7. Tidak mengubah status DRAF/SEMENTARA menjadi FINAL READY semata-mata kerana PDF lulus ujian teknikal.

## Pratonton (PR #440)

Penjana dan ujian baharu hanya untuk **13 fail draf** yang mempunyai sumber berstruktur:

- PSV Tahun 2–6 — 42 PdP setahun.
- RBT Tahun 4–6 — 32 PdP setahun, tarikh A/B masih tidak diketahui.
- Pendidikan Moral Tahun 2–6 — 96 sesi setahun, sumber A/B dikelola dengan ID yang sama.

Semua perubahan dalam `rpt_2027/common/format_2026_layout_preview.py` dan `scripts/build_rpt_2027_standard_preview.py` kekal **pratonton**, tidak dipasang pada Telegram, Web, DB atau kuota. Sebarang penerbitan memerlukan audit visual PDF dan kelulusan kandungan/minggu/tarikh sebelum muat turun pengguna ditukar.

## Sumber rujukan

- Google Drive: `CIKGULAJU_RPT_ENGLISH_TAHUN_6_2027_FORMAT_CONTOH_2026.docx` (struktur Minggu/Tarikh, Unit/Tajuk, CS, LS, Catatan).
- Google Drive: `RPT_Matematik_Tahun_4_SK_2026_Rozayus_Academy.docx` (format 2026 untuk rujukan **susunan sahaja**, jangan menyalin hak cipta atau bahan promosi).
- Repo: `rpt_2027/english`, `rpt_2027/bahasa_melayu`, `rpt_2027/psv`, `rpt_2027/rbt`, `rpt_2027/pendidikan_moral`.
