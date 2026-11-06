# RPH Aktiviti Khas CikguLaju — Koleksi Berperingkat v1

**Status: DRAF UNTUK SEMAKAN; BELUM LIVE di Telegram/Web.**

Koleksi ini menambah aktiviti yang tidak mempunyai nombor Lesson/PdP sukatan biasa. Fail sumber: `catalog_v1.json`.

## Skop

| Jenis | Rekod | Tahun | Catatan |
|---|---:|---|---|
| Program Transisi | 20 | Tahun 1 | 10 Fasa Penyesuaian + 10 Fasa Kesediaan |
| Selepas Tamat Sukatan | 10 | Tahun 1–2 | Versi asas, visual dan manipulatif |
| Selepas Tamat Sukatan | 10 | Tahun 3–4 | Versi pengukuhan, kerjasama dan penaakulan |
| Selepas Tamat Sukatan | 10 | Tahun 5–6 | Versi inkuiri, projek dan analisis |
| **Jumlah** | **50** | | 20 + (10 tema x 3 tahap) |

**Nota penting:** Program Transisi rasmi digunakan khusus untuk Tahun 1. Guru Tahun 2 boleh mengguna aktiviti berunsur suai kenal pada awal persekolahan, tetapi ia mesti dipaparkan sebagai `Aktiviti Awal Persekolahan`, **bukan** `Program Transisi Tahun 2`.

## Dasar kualiti dan integriti

1. Aktiviti ialah teks asal CikguLaju; garis panduan fasa dirujuk daripada **Kit Program Transisi Tahun Satu 2.0 Edisi 2** KPM (2023). Semak semula arahan sekolah dan penyesuaian **Kurikulum Persekolahan 2027** sebelum menerbitkan untuk 2027.
2. Tiada SK/SP, tema rasmi, Unit atau halaman buku teks direka-reka. **Jangan** memadankan rekod aktiviti khas dengan RPT/SOW secara automatik.
3. Simpan data katalog sebagai sumber tambahan; **jangan** menimpa jadual RPH, PdP, RPT/SOW, DB sedia ada, atau rekod pengguna.
4. Setiap aktiviti mempunyai objektif, set induksi, **tiga aktiviti utama yang berasingan**, pengukuhan/penilaian berasaskan bukti, penutup, BBM dan tempoh cadangan.
5. Untuk format Word/PDF: kekalkan satu halaman A4, jadual RPH asal CikguLaju, nombor **Aktiviti 1/2/3 di baris baharu**, tempoh boleh diubah guru. Masa contoh: 5 + 15 + 15 + 15 + 5 + 5 minit.
6. Pelbagai mata pelajaran dalam `subject_options` merupakan cadangan kesesuaian sahaja; guru memilih subjek sebenar jika perlu, tetapi jangan cipta kod sukatan.
7. Semua menu dan API Web/Telegram mesti merujuk **katalog yang sama**, menggunakan fungsi muat turun yang disahkan, tanpa penjanaan AI runtime.

## Aliran UI yang dicadangkan

`Sediakan Bahan PdP → Aktiviti Khas → [Minggu Transisi / Selepas Tamat Sukatan] → Tahun → Aktiviti → Kelas, tarikh, masa → Papar Bahan → Muat Turun RPH Word/PDF`

- Jika `Minggu Transisi`: Tahun 1 sahaja; paparkan Fasa Penyesuaian / Fasa Kesediaan.
- Jika `Selepas Tamat Sukatan`: Tahun 1–6; hanya tunjuk 10 aktiviti untuk tahap Tahun yang dipilih.
- Elak label `Lesson 1` atau `PdP 1` kerana koleksi ini **bukan** sukatan rasmi. Gunakan ID `K01–K20` dan `S01A–S10C` untuk rekod dalaman, bukan nombor RPT.
- Tahun 1 pada sesi 2027 perlu mematuhi sumber kurikulum yang berkuat kuasa; koleksi ini bebas SK/SP sehingga pengesahan.
- Tarikh RPH kepada pengguna: `DD/MM/YYYY`, masa mula/tamat ikut pilihan guru.

## Pintu kelulusan sebelum penerbitan

- [x] 20 aktiviti Transisi dan 30 aktiviti tamat sukatan dibekalkan, tiga tahap mempunyai aktiviti tersendiri.
- [x] Struktur data diperiksa: ID unik, tiga langkah, BBM, objektif dan penilaian ada.
- [ ] Semakan pedagogi guru/penyelaras untuk setiap rekod, termasuk kesesuaian Tahun 1 KP2027.
- [ ] Renderer Word dan PDF sehalaman diuji bagi semua 50 rekod.
- [ ] API bersama dan menu Telegram/Web dilengkapkan.
- [ ] Ujian muat turun sebenar di telefon dan komputer.
- [ ] Ujian bukan-regresi untuk semua laluan RPH biasa serta data asal.
- [ ] Pengesahan staging sebelum sebarang penerbitan ke produksi.

## Sumber rujukan

- KPM: [Kit Program Transisi Tahun Satu 2.0 Edisi 2](https://www.moe.gov.my/storage/files/shares/pekeliling_dan_garis_panduan/surat_siaran/bahagian-pem-kurikulum/Kit%20Program%20Transisi%20Tahun%20Satu%202.0%20Edisi%202.pdf)
- KPM: [Maklumat Kurikulum Persekolahan 2027](https://www.moe.gov.my/storage/files/shares/images/KPM/UKK/2023/12_Dis/Kurikulum%20Persekolahan%202027%20Terkini.pdf)
