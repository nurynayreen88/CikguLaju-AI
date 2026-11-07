# Sains Tahun 6 — gerbang sumber 84 PdP sebelum membina RPH

Tarikh: 7 November 2026. **Staging PR #442 / HOLD.**

## Identiti sumber yang ditemui

1. DSKP Sains Tahun 6 KSSR Semakan 2017, *terbitan Bahagian Pembangunan Kurikulum KPM, September 2021*. Salinan PDF awam: https://beebeeclassroom.com/wp-content/uploads/2022/04/DSKP-KSSR-Semakan-2017-Sains-Tahun-6_ISBN_.pdf. Senarai DSKP juga dipaparkan pada portal sekolah dalam hospital negeri Selangor: https://sites.google.com/moe.gov.my/sdh-selangor/dskp-dokumen-standard-kurikulum-dan-pentaksiran/sains-sr. Keaslian kod SP perlu disahkan per baris; semakan awal bukan kelulusan akademik.
2. Buku Teks Sains Tahun 6 Sekolah Kebangsaan dalam Drive pemilik, fail `GuruBesar_BukuTeks_Sains_T6_SK.pdf` berukuran kira-kira **549 MB**: tidak dapat dibaca secara visual pada aliran semakan ini. Portal DBP memaparkan petikan buku dan maklumat penulis: https://bukuteks.dbp.gov.my/media/media/inFfH6uIfD.pdf; petikan itu **bukan keseluruhan buku** dan tidak membenarkan dakwaan halaman latihan tertentu sudah disahkan.
3. Susunan 84 PdP `SCI-Y6-PDP-001` hingga `SCI-Y6-PDP-084`, daripada fail staged v25.82 yang telah diaudit sebelum ini. Penjana RPT sumber Sains mengekalkan identiti Unit, SK, SP dan tajuk; **tiada sumber DB produksi diubah**.

## Status kerja semasa

`tools/audit_sains_y6_84_source_preflight_20261107.py` memeriksa:

- Kesemua 84 kod PdP unik dan tersusun menaik tanpa ID berulang.
- Kod SP set `2.1–13.1` daripada 17 kumpulan kandungan yang telah dipetakan, dan SK sepadan awalan SP.
- Setiap kod sumber kekal `HOLD`, lengkap Unit/tajuk.
- Tiada halaman buku teks, skor akademik atau status FINAL READY direka.
- Setiap SP mempunyai catatan keselamatan/risiko yang relevan sebelum pembinaan RPH.

Hasil selepas CI berjaya ialah `build/sains_y6_84_preflight_20261107/SAINS_YEAR6_84_STAGING_SOURCE_PREFLIGHT.csv` dan `SUMMARY_YEAR6_HOLD.json`. **Ini belum 84 RPH Tahun 6.**

## Topik kritikal semasa RPH Tahun 6 dibangunkan

| Unit | Risiko dan garis panduan |
|---|---|
| 2 Manusia | Pembiakan dan sistem saraf: bahan visual sesuai umur; lindungi privasi murid, tiada eksperimen menyakitkan |
| 3 Mikroorganisma | Jangan benarkan murid mengkultur mikroorganisma yang tidak diketahui atau memegang makanan berkulat |
| 6 Daya | Geseran/tekanan udara: eksperimen beban ringan, tiada kaca tekanan tinggi atau aktiviti jalan raya |
| 7 Kelajuan | Jarak dan masa diukur selamat, unit rumus konsisten |
| 8 Pengawetan | Gunakan eksperimen yang selamat; tiada pemprosesan makanan berisiko atau hidangan produk tanpa piawaian |
| 10 Gerhana | Jangan arah murid memandang terus ke Matahari tanpa perlindungan khusus |
| 12 Kestabilan/Kekuatan | Pemboleh ubah dikawal; binaan dengan beban kecil dan bahan kitar semula selamat |

**Sebelum >=80% boleh diperakui:** semakan makna SP seorang demi seorang, visual Buku Teks edisi sebenar termasuk aktiviti, pelaksanaan aktiviti guru/murid, bukti PBD, layout Word/PDF A4, dan ujian sebenar Telegram–Web dari sumber sama.

Tidak ada RPH Tahun 6 dikeluarkan kepada pengguna dalam PR ini. Staging sahaja, tanpa auto-merge, deployment, overwrite SQLite atau perubahan langganan.
