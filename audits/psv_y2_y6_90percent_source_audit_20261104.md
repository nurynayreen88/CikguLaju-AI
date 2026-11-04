# Audit kandungan PSV Tahun 2–6 menuju 90% | 4 November 2026

**Peringkat:** DRAF SEMAK LANJUTAN (sasaran penyediaan kandungan ~90%); **BUKAN FINAL READY**. Tiada merge ke `main`, perubahan database produksi, atau pengaktifan Telegram.

## Hasil semakan yang dilaksanakan
| Tahun | Bilangan RPT CSV / HTML | RPH draf | Padanan struktur dan rujukan |
|---|---|---:|---|
| 2 | 1 / 1 | 42 | **42/42 lulus** |
| 3 | 1 / 1 | 42 | **42/42 lulus** |
| 4 | 1 / 1 | 42 | **42/42 lulus** |
| 5 | 1 / 1 | 42 | **42/42 lulus** |
| 6 | 1 / 1 | 42 | **42/42 lulus** |
| **Jumlah** | **5 CSV + 5 HTML** | **210** | **210/210 lulus audit konsistensi** |

**Kaedah:** membaca semula melalui connector GitHub semua 210 fail RPH (secara kelompok) dan baris RPT sepadan; semak tajuk dan nombor PdP, SK dan SP yang sama dengan RPT, tajuk unit, pautan buku teks sebenar, serta kewujudan objektif, set induksi, Aktiviti 1/2, pentaksiran dan penutup. Ini **bukan** audit ketepatan semantik penuh 210 SK/SP, bukan larian CI, dan bukan pengesahan cetakan A4.

## Rujukan asal digunakan
| Tahun | Buku Teks | DSKP |
|---|---|---|
| 2 | https://fliphtml5.com/laiqy/thik/Buku_Teks_Pendidikan_Kesenian_Tahun_2/ | https://drive.google.com/file/d/1RA2bw9IGU9MFakT33HhgAdnjY-7H3DW8/view |
| 3 | https://fliphtml5.com/ubcth/flrm/ | https://drive.google.com/file/d/1asgoqHa5EPOTzhcDz9k5G4WzdGSAg8tY/view |
| 4 | https://fliphtml5.com/jfuhh/hbrx/Buku_Teks_Pendidikan_Kesenian_Tahun_4/ | https://drive.google.com/file/d/1CpSVz8txeDqSnKM7OfOmrjnYH9HBmGy1/view |
| 5 | https://anyflip.com/gygr/pity/basic | https://drive.google.com/file/d/19zvNNKKbn6mIwF7ES9I87yqNaj1xW2Fx/view |
| 6 | https://fliphtml5.com/hkvtu/cnbo/Pendidikan_Seni_Visual_Tahun_6/ | https://drive.google.com/file/d/1-EmxKXK_Fn3tK-wY42ST4TNOIO0CHBHy/view |

Peta 50 unit lengkap (tajuk, bidang/teknik, halaman rujukan, bahan, idea amali dan kod DSKP): `rpt_2027/psv/textbook_dskp_source_map_20261104.json`. Tahun 2–4 Buku Teks Pendidikan Kesenian merangkumi Seni Muzik: RPH ini hanya untuk Seni Visual.

## Isu sumber diselesaikan atau ditandakan
- **Tahun 2**: SP `2.1.3` dicetak **dua kali** untuk bidang berlainan; kekalkan kod bercetak, jangan reka kod `2.1.4`. Projek SK `5.1` dengan SP bercetak `3.3.1`.
- **Tahun 3**: Unit 8 ialah **Cantik Bercahaya** (renjisan dan percikan). SK `5.1` projek mengandungi SP bercetak `3.3.1–3.3.5`.
- **Tahun 4**: Unit 10 buku teks ialah **Harum Mewangi**, ukiran bunga timbul pada sabun (ms 96–99), DSKP `1.1.4, 2.1.9, 3.1.5`. Contoh RPT 2026 mengulangi diorama, jadi buku teks dan DSKP menjadi sumber utama.
- **Tahun 5**: Modul projek SK `5.1` mempunyai **SP `5.1.1–5.1.6`**, termasuk pengemasan akhir `5.1.6`. Buku Unit 10 ialah **Bunga Kemboja Emas** (tekat).
- **Tahun 6**: Unit 4 **Cik Lebah dan Madu** ialah produk kotak pembungkusan 3D, bukan panel lukisan; Unit 5 **Si Cilik Koi** ialah arca stabail 3D yang boleh digunakan sebagai permainan. Unit 10 **Beg Batik Rekaanku**. SK `3.1` merangkumi SP bercetak `3.2.1–3.2.3`; jangan cipta SK `3.2`. SK projek `5.1` mempunyai **SP `5.1.1–5.1.5`**, termasuk `5.1.5` mengemas kawasan selepas pameran. RPH Tahun 6 PdP 026/042 menggunakan `5.1.5` sebagaimana DSKP, bukan `5.1.4`.
- Semasa menghasilkan aktiviti ukiran, tembikar, capan dan model, contoh BBM menggunakan alat tumpul, gam selamat dan bahan tidak toksik sebagai penyesuaian keselamatan kelas.

## Backups dan jaminan bukan-destructive
- Lima set 42 RPH sebelum pembetulan disimpan di `rph_standalone/psv/year{2..6}/backups_pre90_20261104/` (210 backup).
- Tahun 6 mengekalkan juga backup draf awal di `rph_standalone/psv/year6/backups_20261104/`.
- RPT CSV asal sebelum pemetaan disimpan di `rpt_2027/psv/backups/`.
- Semua perubahan berada hanya pada branch PR #196.

## Baki 10% menuju READY
1. Semakan visual **setiap halaman** buku teks dan demonstrasi sebenar kesesuaian bahan/amali; pautan dan julat halaman yang direkod bukan bukti setiap halaman telah disahkan secara visual.
2. Audit **maksud/tafsiran setiap SP** berbanding setiap objektif dan aktiviti, terutama kemahiran 3D Tahun 6 dan cetakan kod bercanggah. Ujian kewujudan kod dan padanan rentetan tidak mencukupi.
3. Semak peruntukan masa 60 minit, pengagihan sesi terhadap jadual sebenar sekolah, pameran mengikut penggal serta takwim Kumpulan A/B 2027 dan cuti negeri.
4. Jana dan periksa visual RPH Word/PDF **satu halaman A4** dan RPT PDF landskap.
5. Jalankan CI (`tests/test_psv_rpt_rph_alignment.py`) dan uji integrasi bot/DB pada staging sebelum sebarang tindakan ke `main`.

**Keputusan:** 210/210 padanan struktur dan sumber **lulus**; kandungan draf disediakan menuju sasaran ~90%, tetapi **status semua RPH/RPT kekal DRAF SEMAK** dan tidak boleh dinaikkan kepada READY sehingga gerbang akhir disahkan.
