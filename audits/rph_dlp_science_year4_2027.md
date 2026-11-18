# RPH Science DLP Year 4 SK 2027

Set ini mengandungi 59 Lesson dan 10 Review dalam 10 unit. Lesson menggunakan 60 minit dan Review menggunakan 30 minit, dengan jumlah 3,840 minit atau 64 jam. Setiap RPH memaparkan tarikh Kumpulan A/B, tajuk, CS/LS, rujukan buku bercetak, langkah guru dan murid serta evidens pentaksiran. Sesi Review menggunakan LS yang telah diajar dalam unitnya.

## Sumber

- [RPT Science DLP Year 4 2027](../rpt_2027/dlp/CikguLaju_RPT_DLP_2027_Science_Year_4.docx) ialah RPT asal yang diterbitkan melalui #882 dan #883. Penjana memadankan kesemua 69 baris pada tarikh, tajuk, unit, CS/LS, objektif, halaman buku dan tempoh. SHA-256 RPT asal digunakan untuk mengesan pindaan.
- 92 kod LS dipadankan dengan [DSKP KSSR Science Year 4 (Revised 2017), edisi DLP](https://asiemodel.net/wp-content/uploads/2022/08/DSKP-KSSR-Semakan-2017-Science-Year-4.pdf). Rujukan buku mengikut nombor halaman bercetak dalam [Science Year 4 BT074003](https://anyflip.com/yjsfa/rjal/basic/), yang disenaraikan dalam [E-Katalog KPM](https://moe.gov.my/storage/files/shares/Banner/E-Katalog%20Buku%20Teks%20KPM.pdf).

## Evidens dan perubahan

| Lesson | Rujukan | Evidens murid |
| --- | --- | --- |
| 11 | LS 2.1.1–2.1.2, hlm. 24–28 | Label laluan udara masuk dan keluar. Lukis arah oksigen masuk ke darah dan karbon dioksida keluar daripada darah di paru-paru. |
| 30–31 | LS 5.1.3–5.1.4, hlm. 92–93 | Catat lebar bayang dalam cm. Bandingkan kedudukan lampu dan skrin dalam dua ujian saiz. Bandingkan orientasi kad dan kedudukan lampu terhadap silinder dalam dua ujian bentuk. Label lakaran dan terangkan laluan lurus cahaya. |
| 35 | LS 5.3.3–5.3.4, hlm. 102–104 | Rekod jalur warna pada kad atau foto hasil demonstrasi. Terangkan bagaimana cahaya putih berpisah kepada warna dalam titisan hujan. Guru mengawal lampu suluh bateri dan memantulkan cahaya ke kad jauh daripada wajah. |
| 43 | LS 7.1.5–7.1.6, hlm. 132–133 | Label input dan output tenaga dalam rajah. Nyatakan prinsip keabadian tenaga dan jejak haba atau bunyi ke persekitaran. |
| 46 | LS 8.1.1–8.1.3, hlm. 142–144 | Susun kad di bawah tumbuhan, haiwan, batuan atau petroleum. Gunakan pasir sebagai bahan untuk kaca dalam kumpulan batuan. Kelaskan lima kad baharu secara individu dan jelaskan satu padanan objek, bahan dan sumber. |
| 47–49 | LS 8.2.1, hlm. 145–150 | Catat serapan dan apungan berasingan. Bandingkan nyalaan LED litar bateri dengan cahaya yang melepasi sampel. Gunakan bacaan haba yang disediakan guru dan ukuran panjang untuk menyokong kesimpulan tentang pengaliran haba dan keanjalan. |
| 52 | LS 9.2.1–9.2.2, hlm. 160–162 | Lukis arah dan nyatakan tempoh putaran serta peredaran Bumi dari sudut pandang yang sama. |

Pembetulan Lesson 46 menggantikan tafsiran awal tentang lima sumber. Nota DSKP hlm. 64 menyenaraikan tanah di bawah batuan. [Buku teks hlm. 142–144](https://anyflip.com/ejbrb/wxvo/basic/151-198) menggunakan pasir dan botol kaca sebagai contoh dalam kumpulan itu. Objektif daripada RPT asal menyenaraikan empat sumber dan digunakan dalam RPH.

## Fail dan status

Jalankan `python -m staging.dlp.year4.render_science --output <folder>` untuk menghasilkan Word dan PDF. Semakan setempat meliputi kesemua 69 fail Word yang ditukar ke PDF dan 69 PDF penjana. Setiap RPH muat satu halaman A4.

Draf laluan aplikasi menggunakan penjana yang sama, dengan medan kelas, tarikh, masa, bilangan murid dan refleksi daripada aliran sedia ada. Katalog menyemak pasangan unit dan ID pelajaran.

## Keputusan penerbitan

- Kelulusan guru bagi komit `786f6980fc3a` direkodkan pada 18 November 2026 selepas pengesahan pemilik dalam perbualan.
- [CI eksport Word/PDF](https://github.com/nurynayreen88/CikguLaju-AI/actions/runs/44279407083) lulus pada percubaan semula. Semakan aplikasi juga lulus dengan sesi simulasi pada [#933](https://github.com/nurynayreen88/CikguLaju-AI/pull/933) dan [#939](https://github.com/nurynayreen88/CikguLaju-AI/pull/939).
- [PR ujian akaun guru #940](https://github.com/nurynayreen88/CikguLaju-AI/pull/940) lulus ujian akses dan cap SHA-256 untuk empat fail Lesson 46 dan Review 08. Deploy Google staging `dep-dbunhdqjnfac73dq1hu0` aktif pada 18:08 MYT dengan binaan `3fe5fee38407`. Pelayar sampai ke halaman log masuk. Sesi guru dan muat turun sebenar belum disahkan.

**HOLD ujian akaun guru.** Set menunggu pengesahan muat turun Word/PDF menggunakan akaun guru sebenar sebelum penerbitan.

## Edisi bilik darjah

Pakej edisi bilik darjah menggunakan turutan dan objektif bagi 69 sesi dalam RPT asal. RPT memadankan setiap sesi dengan RPH melalui tajuk, tarikh Kumpulan A/B, CS/LS, halaman buku, tempoh, objektif dan kriteria kejayaan murid. Sepuluh Review mempunyai nombor dan kod LS khusus daripada pelajaran yang telah diajar. Tujuh minggu fleksibel mempunyai cadangan tindakan mengikut rekod PBD sekolah. Perancangan teras kekal 3,840 minit.

- Lesson 08 dan 09 menggunakan julat yang sama bagi Kumpulan B, 2–4 Februari. Lampiran C memperuntukkan 5 Februari sebagai cuti tambahan KPM. [Kalendar akademik KPM 2027, Lampiran A–C](https://www.moe.gov.my/storage/files/shares/pekeliling_dan_garis_panduan/surat_siaran/SS%20KPM%20Bil.%201%20Tahun%202026%20-%20Kalendar%20Akademik%20Tahun%202027.pdf)
- Lesson 18 menghubungkan pengambilan alkohol dengan respons yang lambat. Lesson 19 menamakan spirakel pada serangga. Lesson 25 menerangkan glukosa, penyimpanannya sebagai kanji dan pelepasan oksigen. [Buku teks BT074003, hlm. 46, 54 dan 78](https://anyflip.com/ejbrb/wxvo/basic/51-100)
- Lesson 53 menghubungkan putaran Bumi dengan siang dan malam, perubahan ketara kedudukan Matahari serta perubahan panjang dan arah bayang. [DSKP Science Year 4, hlm. 69](https://asiemodel.net/wp-content/uploads/2022/08/DSKP-KSSR-Semakan-2017-Science-Year-4.pdf#page=81)
- Contoh data guru dalam Review 01 dan Review 08 membolehkan murid mengemukakan bukti tanpa perlu mencari jadual tambahan. Data contoh khusus turut disediakan untuk murid yang memerlukan pilihan duduk dalam Lesson 14 dan untuk perbandingan haba dalam Lesson 49.

[Word dan PDF edisi bilik darjah](../staging/dlp/year4/bahan_guru) mengandungi buku RPT dan buku RPH. Untuk menjana semula kedua-dua buku serta folder satu fail bagi setiap sesi dan format, jalankan `python -m staging.dlp.year4.teacher_pack <folder>`. Penerbitan aplikasi direkodkan berasingan daripada penyerahan bahan terus kepada guru. Kelulusan versi `786f698` merujuk kepada edisi terdahulu.
