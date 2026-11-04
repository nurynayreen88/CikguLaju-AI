# Pengesahan Buku Teks PSV Tahun 2–6 — 5 Nov 2026

**Skop:** PR #267, 210 RPH (42 PdP setiap tahun). Semakan ini menambah bukti rujukan; **bukan kelulusan penerbitan**. Jangan merge / deploy / ubah `main` atau Telegram LIVE berdasarkan laporan ini sahaja.

## Kaedah dan batas bukti
1. Banding peta sumber `rpt_2027/psv/textbook_dskp_source_map_20261104.json` dengan judul dan susunan unit dalam buku digital serta sumber RPT yang relevan.
2. Periksa dokumen DSKP asal Tahun 2–6 daripada Google Drive; banding semantik kod dan tindakan untuk kes berisiko.
3. Baca terus 6 RPH calon (T2 PdP027, T3 PdP017, T4 PdP039, T5 PdP039, T6 PdP034/039) dan padankan dengan bukti buku/DSKP yang boleh dibuka.
4. CI 27/27 dan `210/210` page-anchor sudah lulus pada commit `af16c396` (run 41931756141); ini **hanya** mengesahkan pemetaan RPH kepada peta sumber, **bukan** pembacaan visual setiap helaian buku oleh penyemak. Tidak boleh didakwa audit individu 210/210.

## Inventori Buku Teks dan pengesahan tajuk
| Tahun | Buku digunakan | Susunan 10 unit | Pemetaan halaman | Status bukti |
|---|---|---|---|---|
| 2 | [Pendidikan Kesenian Tahun 2 SK](https://fliphtml5.com/laiqy/thik/Buku_Teks_Pendidikan_Kesenian_Tahun_2/) | 10/10 disemak daripada kandungan buku | Bahagian Seni Visual dipetakan; keseluruhan unit merangkumi Muzik juga | SUSUNAN SAH; halaman individu belum semuanya disemak |
| 3 | [Pendidikan Kesenian Tahun 3 SK](https://fliphtml5.com/ubcth/flrm/) | 10/10 disemak daripada kandungan buku | Bahagian Seni Visual dipetakan | SUSUNAN SAH; halaman individu belum semuanya disemak |
| 4 | [Pendidikan Kesenian Tahun 4 SK](https://fliphtml5.com/jfuhh/hbrx/Buku_Teks_Pendidikan_Kesenian_Tahun_4/) | 10/10 disemak daripada kandungan buku | Unit 10 ms 96–99 disemak langsung | SUSUNAN SAH; semakan unit terpilih |
| 5 | [Pendidikan Seni Visual Tahun 5 SK](https://anyflip.com/gygr/pity/basic) | 10/10 disokong senarai [eCentral](https://ecentral.my/buku-teks-psv-tahun-5/) dan [RPT 2024–2025](https://anyflip.com/zxzlm/ivxv/basic) | Unit 10 tekat ms 82–89 disokong RPT | SOKONGAN SEKUNDER; PDF buku penuh masih perlu audit visual langsung |
| 6 | [Pendidikan Seni Visual Tahun 6 SK](https://fliphtml5.com/hkvtu/cnbo/Pendidikan_Seni_Visual_Tahun_6/) | 10/10 disemak daripada kandungan buku | Jadual kandungan ms 8–87 jelas, unit 4, 9 dan 10 dirujuk langsung | SUSUNAN SAH; semakan unit terpilih |

**Nota:** Buku Tahun 2–4 memuatkan Pendidikan Kesenian (Seni Visual **dan** Seni Muzik). RPH PSV hendaklah merujuk bahagian Seni Visual, bukannya menganggap setiap halaman unit ialah aktiviti seni visual.

## Semakan kritikal disokong sumber langsung
- **Tahun 2 PdP027 / Unit 7 Burung Kenek-kenek:** RPH merujuk bahan model topeng dan pembentukan paruh kadbod selamat; tajuk/unit wujud pada buku (Unit 7 ms 56–63; peta PdP pada ms 56–59). Penyemakan terperinci semua arahan bergambar masih terbuka.
- **Tahun 3 PdP017 / Unit 5 Pahlawan Kecil:** buku ms 40 memaparkan *Parang Ilang*, struktur dan konteks alat pertahanan diri. RPH membina **model kadbod tidak berfungsi**, bukan senjata sebenar. Ini adaptasi keselamatan, bukan arahan buku verbatim.
- **Tahun 4 PdP039 / Unit 10 Harum Mewangi:** buku ms 96–99 menerangkan ukiran timbul bunga kemboja pada sabun, alur motif, turunkan latar, bersihkan dan hias dengan kain net/reben. RPH mengekalkan langkah seni tersebut dan menggantikan pisau ukir murid dengan alat tumpul. Tidak boleh dilabel diorama.
- **Tahun 5 PdP039 / Unit 10 Bunga Kemboja Emas:** RPT dan DSKP menyokong *tekat* dengan mempulur dan benang, bukannya menampal benang sekadar corak. Buku penuh pada ms 86–87 **belum** diperiksa secara visual terus; kekal berstatus bukti sekunder.
- **Tahun 6 PdP034 / Unit 9 Wau Bulan Sirih Pinang:** buku ms 68–75 menggunakan model wau 3D, motif cerminan, kadbod/kain felt, tampalan, rambu; RPH ms 74–75 menyokong folio, foto atau lakaran akhir, apresiasi dan galeri mini sebagai adaptasi.
- **Tahun 6 PdP039 / Unit 10 Beg Batik Rekaanku:** buku ms 76–87 memperlihatkan aktiviti beg batik dan apresiasi; RPH mengambil bahan proses dan menghasilkan dokumentasi 5 bahagian bagi DSKP `3.1.1`. Gambar akhir tidak boleh menggantikan folio sendiri.

## DSKP asal — kewujudan/semantik kod
- T2 [DSKP](https://drive.google.com/file/d/1RA2bw9IGU9MFakT33HhgAdnjY-7H3DW8/view): di bawah SK `5.1 Persembahan hasil karya`, buku DSKP mencetak SP `3.3.1`.
- T3 [DSKP](https://drive.google.com/file/d/1asgoqHa5EPOTzhcDz9k5G4WzdGSAg8tY/view): di bawah SK `5.1`, DSKP mencetak SP `3.3.1` sehingga `3.3.5`.
- T4 [DSKP](https://drive.google.com/file/d/1CpSVz8txeDqSnKM7OfOmrjnYH9HBmGy1/view): di bawah SK `5.1`, DSKP mencetak SP `3.3.1` sehingga `3.3.5`. **Jangan 'betulkan' kepada `5.1.x` tanpa kuasa sumber.**
- T5 [DSKP](https://drive.google.com/file/d/19zvNNKKbn6mIwF7ES9I87yqNaj1xW2Fx/view): kod projek bermula `5.1.1`; karya unit tekat `3.1.5`.
- T6 [DSKP](https://drive.google.com/file/d/1-EmxKXK_Fn3tK-wY42ST4TNOIO0CHBHy/view): `3.1.1` ialah **folio bahasa seni visual**; `3.2.3` ialah gambar karya akhir secara manual/digital; projek `5.1.1` meliputi bahan folio dan karya. Dua kod ini tidak boleh dianggap sama.

## Keputusan dan gerbang seterusnya
- **DISAHKAN SETAKAT INI:** semua tajuk/susunan 10 unit bagi T2/T3/T4/T6 bersumber buku; T5 10 tajuk bersumber silang RPT/senarai dan perlu visual buku. Enam RPH berisiko telah diperiksa terhadap sumber yang dapat dibaca; semakan kes T5 kekal bukti sekunder.
- **BUKAN DISAHKAN:** visual 210 PdP satu per satu, kandungan semua halaman terlibat, setiap alat/teknik/soalan dalam buku dan ujian Word/PDF native Telegram staging.
- **PENERBITAN:** kekalkan DRAF, `psv_release_approval.json` tidak diwujudkan, jangan tukar status kepada READY. Ujian CI di head selepas commit audit mesti lulus semula sebelum review penerbitan.
- Tiada perubahan ke `app.py`, database, Supabase, pembayaran, referral, Telegram, Render atau `main` dibuat melalui audit ini.
