# Sains Tahun 2–3 — Semakan 96 halaman Buku Aktiviti (7 November 2026)

**STAGING / HOLD** — PR [#442](https://github.com/nurynayreen88/CikguLaju-AI/pull/442). Tidak mengubah Telegram/Web produksi, DB, akaun, langganan, skor akademik atau status READY.

## Sumber

- Buku Aktiviti Sains SK Tahun 2, 89 halaman PDF: https://drive.google.com/file/d/1j0qoRWHcaAzHVgbb6uua7k_3i2-qVm0v/view
- Buku Aktiviti Sains SK Tahun 3, 98 halaman PDF: https://drive.google.com/file/d/1kVL3PT-VjQiITqmfNXlURQA8gLYvCrI5/view

Semakan dibuat melalui **imej penuh pada halaman latihan asal**, bukan meneka berdasarkan indeks kandungan. Halaman buku yang dinyatakan dalam RPH ialah **nombor bercetak**: Tahun 2 pPDF = m/s+4 dan Tahun 3 pPDF = m/s+5.

## Liputan dan status bukti

| Audit | Tahun 2 | Tahun 3 | Jumlah |
|---|---:|---:|---:|
| Identiti PdP/SP sah daripada staging | 51 | 45 | 96 |
| Halaman, tajuk dan label SP latihan diperiksa | 51 | 45 | 96 |
| Panduan penggunaan kandungan latihan khusus | 51 | 45 | 96 |
| Kod SP buku sama dengan kod PdP | 49 | 45 | 94 |
| Latihan berkaitan sahaja, bukan PBD SP | 2 | 0 | 2 |
| Pengesahan guru/panitia | 0 | 0 | 0 |

11 panduan terdahulu ada dalam `audits/sains_y2_y3_ba_page_content_safety_review_20261107.json`. **85 panduan baharu** (43 T2 + 42 T3) disimpan sebagai rekod berasingan dan tidak menimpa semakan dahulu:

- `audits/sains_y2_43_remaining_page_content_20261107.json`
- `audits/sains_y3_42_remaining_page_content_20261107.json`

Setiap rekod mempunyai identiti PdP dan SP, tajuk serta halaman bercetak, pemerhatian spesifik daripada latihan yang dilihat, cadangan tindakan murid, risiko/penyesuaian jika perlu, dan penanda `teacher_academic_approved=false`. Angka **96 disemak isi** menerangkan peliputan editorial terhadap halaman/soalan buku, **bukan pengesahan kualiti akademik RPH atau keberhasilan PdP dalam kelas**.

## Keselamatan dan kecermatan isi

1. **Tahun 2 SP3.1.3, m/s16:** buku meminta menimbang dan mengukur murid serta merekod nama rakan. Cadangan guru menggunakan **data rekaan**, bukan data ukuran peribadi murid; SP rasmi tentang perbezaan tumbesaran dikekalkan.
2. **Tahun 2 SP8.1.4/8.1.5, m/s62:** buku memaparkan air panas, gula kiub/halus dan pengacauan. Murid menafsir gambar/perbandingan; **tiada penggunaan air panas murid**.
3. **Tahun 2 SP9.1.2, m/s65:** latihan asal menunjukkan pisau pemotong botol plastik. Penggunaan pisau dan penyediaan bahan ialah **tugas guru**; murid menilai arah air pada gambar sahaja.
4. **Tahun 2 SP7.1.5, m/s51:** gambar paku dan objek pengalir. Uji secara gambar/kit sel kering rendah voltan; jangan menyentuh paku tajam.
5. **Tahun 3 SP8.1.2, m/s72:** buku menyebut ujian rasa serta sentuhan bagi bahan berasid/beralkali. RPH secara jelas **melarang merasa atau menyentuh bahan ujian** dan menggunakan data litmus sahaja.
6. **Tahun 3 SP8.1.4, m/s76:** contoh sengatan dan bahan alkali. Gunakan gambar untuk mengenal kegunaan bahan; jangan memberi rawatan DIY atau menyapu bahan kimia pada kulit.
7. **Tahun 3 SP5.1.3, m/s50:** cara keratan menggunakan pisau. Pemotongan hanya dilakukan guru; murid menafsir urutan melalui carta.
8. **Tahun 3 SP10.1.4/10.1.5, m/s90/92:** model takal/kren. Guna model beban ringan dan lukisan, bukan pengangkatan beban sebenar.
9. **Dua rujukan berkaitan sahaja:** Tahun 2 SP4.1.7 (buku m/s27 berlabel SP4.1.5) dan SP6.1.6 (buku m/s44 berlabel SP6.1.5). Latihan tersebut **tidak** dijadikan tugasan PBD SP yang salah. Bukti PBD sebenar datang daripada aktiviti utama RPH masing-masing.

## Gerbang pelaksanaan

`tools/sains_buku_aktiviti_mapping_20261107.py` kini menolak sumber yang hilang salah satu daripada **96 panduan** atau bertukar tahun, kod PdP, SP, tajuk atau halaman. Ia turut menolak promosi bahan berkaitan sahaja menjadi tugasan PBD SP dan mengekalkan semua `page_content_teacher_signoff=MISSING`. Penjana RPH Tahun 2–3 membaca panduan ini untuk menambah nota penggunaan Buku Aktiviti pada hasil Word/PDF.

`tools/check_sains_ba_96_document_content_20261107.py` menyemak 96 Word dan 96 PDF **yang benar-benar dijana**, termasuk tajuk, m/s, amaran PBD, dan panduan kandungan per PdP. CI juga mencetak Word melalui LibreOffice bagi memastikan satu halaman A4.

### Apa yang belum selesai

- Penilai guru/panitia perlu mengesahkan *kesesuaian* setiap tugasan dan penyesuaian keselamatan untuk SP, bukan semata-mata kod SP bercetak.
- Perlu pengesahan halaman **Buku Teks** dan keserasian sumber RPT/DSKP semua PdP; isu asal Tahun 2 SP3.1.3/10.1.6 masih perlu keputusan pengarang/semakan akademik.
- **Ujian sebenar** laluan buku/aktiviti melalui profil guru dan RPH di Web/Telegram staging belum dibuat; data baharu tidak diaktifkan dalam sistem LIVE.
- Sasaran ≥80% kualiti kurikulum dan READY **tidak diperakui**. Semua 342 PdP Sains dalam program keseluruhan kekal HOLD.

**Tiada auto-merge, tiada deploy, tiada DB overwrite/reset.**
