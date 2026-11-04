# Audit PSV Tahun 2–6: sasaran kandungan 90% (4 November 2026)

**Status:** kandungan dibangunkan hingga tahap semakan lanjutan; 90% ialah **sasaran pembangunan**, bukan markah lulus atau dakwaan 90% setiap aktiviti telah disahkan secara visual. **Tidak READY dan tidak LIVE.**

## Sumber disahkan
| Tahun | DSKP dalam Drive | Buku Teks digital | Isu sumber terpenting |
|---|---|---|---|
| 2 | https://drive.google.com/file/d/1RA2bw9IGU9MFakT33HhgAdnjY-7H3DW8/view | https://fliphtml5.com/laiqy/thik/Buku_Teks_Pendidikan_Kesenian_Tahun_2/ | DSKP bercetak SP `2.1.3` dua kali, bukannya `2.1.4`; buku ialah Pendidikan Kesenian gabungan seni visual dan muzik, hanya komponen seni visual dirujuk |
| 3 | https://drive.google.com/file/d/1asgoqHa5EPOTzhcDz9k5G4WzdGSAg8tY/view | https://fliphtml5.com/ubcth/flrm/ | DSKP `1.1.10` memang wujud untuk model alat pertahanan diri; buku Unit 8 bernama **Cantik Bercahaya** |
| 4 | https://drive.google.com/file/d/1CpSVz8txeDqSnKM7OfOmrjnYH9HBmGy1/view | https://fliphtml5.com/jfuhh/hbrx/Buku_Teks_Pendidikan_Kesenian_Tahun_4/ | Buku Teks Unit 10 **Harum Mewangi** halaman 96–99 mengajar **ukiran timbul**, dengan `1.1.4`, `2.1.9`, `3.1.5`; contoh RPT tersalah salin diorama `1.1.3`, `2.1.8` |
| 5 | https://drive.google.com/file/d/19zvNNKKbn6mIwF7ES9I87yqNaj1xW2Fx/view | https://anyflip.com/gygr/pity/basic | DSKP gabungan teknik `2.1.1`–`2.1.10`, projek `5.1.1`–`5.1.5` |
| 6 | https://drive.google.com/file/d/1-EmxKXK_Fn3tK-wY42ST4TNOIO0CHBHy/view | https://fliphtml5.com/hkvtu/cnbo/Pendidikan_Seni_Visual_Tahun_6/ | DSKP SK penghasilan **3.1** walaupun SP `3.2.1`–`3.2.3`; projek `5.1.1`–`5.1.4` sahaja |

## Pembetulan khusus Buku Teks dan DSKP
- Tahun 4 Unit 10 dikekalkan sebagai **Harum Mewangi**, teknik ukiran bunga timbul pada sabun menggunakan alat tumpul dan pengawasan, mengikut buku; konflik diorama ialah **ralat salin pada contoh RPT**, bukan unit pengayaan CikguLaju.
- Tahun 6 Unit 4 **Cik Lebah dan Madu**: Buku Teks ms 26–33 menghasilkan kotak pembungkusan makanan 3D, penggunaan lukisan/lipatan/cantuman, kemasan reben. RPH 010–013 diselaraskan. Bukannya panel gambar.
- Tahun 6 Unit 5 **Si Cilik Koi**: Buku Teks ms 34–45 menghasilkan arca stabail ikan koi berfungsi sebagai permainan, media kadbod/penggulung tisu/cat; untuk murid ganti pistol perekat panas dengan gam selamat. RPH 014–018 diselaraskan.
- Tahun 6 PdP 026 dan 042: SP pameran `5.1.5` yang tidak terdapat dalam DSKP Tahun 6 ditukar kepada `5.1.4` dan diselaraskan pada RPT.
- Standard `1.1.10` Tahun 3 disahkan wujud; kod bercetak `2.1.3` Tahun 2 dikekalkan berdasarkan sumber, dengan catatan rangkap pendua.

## Audit kuantitatif dijalankan
- **210/210** laluan fail RPH sepadan dengan 210 baris dalam lima CSV RPT (42 setiap tahun), tiada nombor PdP hilang.
- Semua kod SK/SP yang tertera dalam 210 baris RPT mempunyai sekurang-kurangnya satu padanan rentetan dalam DSKP tahun masing-masing (**0 kod tidak ditemui**). Ini hanya ujian kewujudan kod dan **bukan pengesahan bahawa tafsiran kod sesuai dengan aktiviti**.
- RPT CSV/HTML lima tahun tersedia. RPH asal Tahun 6 diarkibkan. Tiada perubahan pada `main`, DB utama atau Telegram.
- Ujian struktur Python `tests/test_psv_rpt_rph_alignment.py` disimpan di repository, tetapi **belum ada larian CI berjaya pada head ini**.

## Belum diluluskan / baki menuju READY
1. Tinjauan visual setiap halaman dan aktiviti Buku Teks serta kualiti proses 210 RPH (khususnya bahan setiap projek).
2. Semakan **padanan makna** setiap SP dengan tujuan PdP, bukan sekadar kod wujud. Juga semak pecahan PdP Tahun 6 berbanding peruntukan masa buku teks.
3. Penyelarasan slot pameran pertengahan/akhir untuk Tahun 2–5 dan 2027 kalendar Kumpulan A/B termasuk cuti negeri/cuti gantian.
4. Paparan RPH Word/PDF A4 satu halaman dan RPT PDF landskap, ujian cetakan/visual, ujian CI serta integrasi Telegram.
5. Sebelum READY, audit keselamatan amali sebenar, keupayaan guru dan bahan pengganti bagi murid.

**Keputusan:** hasil ini ialah **DRAF LANJUTAN** menuju sasaran 90%, tidak dilabel FINAL READY sehingga bukti semakan kandungan & ujian cetakan lengkap.
