# Audit Matematik SK Tahun 2 dan 3 DPK Edisi 3 2027

Set pilihan ini menggunakan Dokumen Penjajaran KSSR (Semakan 2017) Edisi 3 untuk Matematik Tahap I. Perenggan 4 Surat Siaran KPM Bil. 6 Tahun 2024 memberi guru pilihan menggunakan DPK Edisi 3 atau DSKP KSSR (Semakan 2017). Pilihan ini dilabel dalam RPT dan RPH. Pemetaan DSKP yang digunakan oleh Web dan Telegram dikekalkan. [Surat siaran KPM](https://www.moe.gov.my/surat-siaran-kpm-bil-6-tahun-2024) · [Halaman rasmi DPK Edisi 3](https://www.moe.gov.my/dokumen-penjajaran-kurikulum-standard-sekolah-rendah-kssr-semakan-2017-edisi-3-bm-bi-sains-matematik-tahap-i) · [Dokumen Matematik Tahap I](https://drive.google.com/file/d/1vjNjPj_rWoEHugtdtMu1c8pNj7MtLVxn/view).

| Set | Kod asas SP disahkan | Rujukan DPK bercetak | Agihan |
| --- | ---: | --- | --- |
| [Tahun 2](../staging/matematik/tahun2/) | 45 | Hlm. 19–35, termasuk 1.1.1(i) dan (ii) | 117 Lesson, 96 jam, 8 unit |
| [Tahun 3](../staging/matematik/tahun3/) | 50 | Hlm. 39–61, termasuk 1.1.1(i) dan (ii) | 117 Lesson, 96 jam, 9 unit |

Setiap tahun mempunyai 42 sesi 30 minit dan 75 sesi 60 minit. RPT menyenaraikan 44 minggu dengan tarikh Kumpulan A/B. Pentaksiran diperuntukkan pada minggu 18. PdP baharu selesai pada minggu 38, 17–21 Oktober bagi Kumpulan A dan 18–22 Oktober bagi Kumpulan B. [Agihan 2027](../staging/matematik/rpt_2027_agihan.json) · [Draf asal #918](https://github.com/nurynayreen88/CikguLaju-AI/pull/918).

## Pembetulan kandungan

| Tahun dan Lesson | Pembetulan dan asas semakan |
| --- | --- |
| Tahun 2, 001–014 | Nyatakan kriteria dan jawapan PBD dalam RPT dan RPH daripada rekod yang sama. Asingkan kriteria, refleksi dan tindakan susulan di dalam RPH. |
| Tahun 2, 010–011 | Gantikan contoh sela seratus dengan sela sepuluh bagi pola menaik dan menurun. DPK hlm. 21 menetapkan selang satu, dua, lima dan sepuluh dalam catatan SP 1.3.1. |
| Tahun 2, 013 | Sediakan pilihan nombor bagi tempat kosong supaya setiap tugas susunan mempunyai satu jawapan tepat. Kekalkan kedua-dua SP 1.1.2 dan 1.1.3 pada hlm. 20. |
| Tahun 2, 111 | Gunakan SP 7.1.2 bagi bentuk asas pada permukaan pepejal. Nilai juga satu ciri bentuk rata di bawah SP 7.2.1. DPK hlm. 34. |
| Tahun 3, 052 | Kedua-dua item menilai penambahan tiga nilai wang dan menggunakan jumlah RM971 serta RM1 575. DPK hlm. 49. |
| Tahun 3, 069–071 | Nyatakan penanda pagi atau petang pada Lesson 069. Lesson 070–071 menggunakan 1 minit bersamaan 60 saat. Kekalkan nilai ini kerana contoh ketiga bercetak pada DPK hlm. 52 tersilap menyamakan 60 minit dengan 60 saat. |
| Tahun 3, 117 | Minta murid memadankan set data yang sama pada piktograf, carta palang dan carta pai. Ketiga-tiganya tertera dalam SP 9.2.2 pada DPK hlm. 61. |

Rujukan buku teks sedia ada menggunakan halaman bercetak. Semakan sumber set ini mengutamakan kod dan halaman DPK serta tugasan yang dipinda. Pengesahan setiap halaman buku teks dan penilaian pelaksanaan masa di bilik darjah masih terbuka. [Tahun 2 Jilid 1](https://fliphtml5.com/lwbmp/epdf) · [Tahun 2 Jilid 2](https://pubhtml5.com/qtnz/fvhe/basic/) · [Tahun 3 Jilid 1](https://anyflip.com/mkqv/kqav/basic) · [Tahun 3 Jilid 2](https://fliphtml5.com/jfuhh/feev/Buku_Teks_Matematik_Tahun_3_Jilid_2/).

## Pengesahan setempat

- 234 padanan RPT/RPH diperiksa untuk ID, tajuk, minggu, tarikh A/B, tempoh, SK/SP, halaman DPK, rujukan buku yang dicetak dan evidens PBD. Jumlah empat fasa diperiksa terhadap tempoh setiap RPH. Liputan kod dan padanan halaman DPK ditentusahkan semula terhadap PDF sumber.
- 234 PDF asal dan 234 Word yang ditukar melalui LibreOffice muat satu halaman A4 setiap dokumen. Dua RPT PDF berorientasi landskap dan masing-masing mempunyai 14 halaman. Susun atur sampel Word, PDF dan halaman pertama kedua-dua RPT diperiksa secara visual.
- 17 ujian regresi bagi menu RPH 2027 Telegram, pilihan masuk dan penghantaran RPT Matematik lulus.
- Set ini tersedia melalui penjana di direktori staging. Pilihan DPK belum disambungkan kepada pemilih atau muat turun guru di Web dan Telegram.

Jalankan arahan ini dari akar repositori. Bagi Tahun 3, gantikan nombor tahun pada nama modul dan laluan keluaran dengan `3`.

```sh
PYTHONPATH=. python -m staging.matematik.tahun2.eksport_tahun2 --output /tmp/matematik-sk-dpk-t2
PYTHONPATH=. python -m staging.matematik.tahun2.eksport_rpt --output /tmp/matematik-sk-dpk-t2/RPT.pdf
```
