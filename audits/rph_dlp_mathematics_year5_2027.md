# RPT dan RPH Mathematics DLP Year 5 SK 2027

Set semakan guru mengandungi 61 Lesson bernombor dan lapan Review dalam lapan unit. Jumlahnya 5,760 minit atau 96 jam. Nombor, turutan, tempoh, tarikh Kumpulan A/B, CS/LS dan hasil pembelajaran yang ditaksir diambil daripada [RPT Mathematics DLP Year 5 SK 2027](../rpt_2027/dlp/CikguLaju_RPT_DLP_2027_Mathematics_Year_5.docx) pada `main`. PdP tamat pada Minggu 38.

Kesemua 72 kod LS sepadan dengan DSKP KSSR Semakan 2017 edisi Inggeris [bahagian awal](https://anyflip.com/nuzm/cvag/basic/) dan [bahagian akhir](https://anyflip.com/nuzm/cvag/basic/51-82). Rujukan halaman mengikut cetakan [Mathematics Year 5 BT085003, DBP 2020](https://fliphtml5.com/mlzri/uxbp/Mathematic_T5_DLP_SK/) yang disenaraikan dalam [E-Katalog KPM](https://moe.gov.my/storage/files/shares/Banner/E-Katalog%20Buku%20Teks%20KPM.pdf).

## Pembetulan rujukan buku

Draf RPT dan RPH menggunakan 23 julat atau rujukan bercetak yang disemak semula. Perubahan penuh disimpan dalam `reference_corrections` pada [data rancangan](../staging/dlp/year5/mathematics_2027.json). Contohnya, Lesson 18 menggunakan halaman 70–72 untuk pembundaran perpuluhan, Lesson 30 menggunakan 104–106 untuk simpanan, pelaburan dan faedah, Lesson 32 menggunakan 110–114 untuk penyelesaian masalah wang dan Lesson 45 menggunakan 199–200 untuk penukaran mililiter dan liter. Review Unit 3 merujuk halaman 115 dan 117 untuk baki wang dan perbandingan pembayaran.

Setiap RPH mempunyai tindakan guru dan murid, bahan, tugasan individu dan contoh jawapan PBD. Lesson 33 menggunakan bilangan hari untuk tempoh merentas bulan atau tahun, termasuk 29 Februari bagi tahun lompat. Lesson 49 membezakan sisi, bucu, paksi simetri, sudut pedalaman dan pepenjuru pada poligon sekata. Kod Review terhad kepada LS yang telah diajar dalam unit tersebut.

## Pengesahan dan eksport

- 69 pasangan RPT/RPH sepadan pada nama sesi, tarikh, minit, CS/LS, halaman buku dan fokus PBD. Kesemua RPH Word dan PDF asli mempunyai satu halaman A4. Word disemak melalui render LibreOffice. RPT Word yang dirender mempunyai lapan halaman A4 landskap.
- Jalankan `PYTHONPATH=. python -m staging.dlp.year5.render_mathematics --output /tmp/rph-dlp-year5`. Penjana menyemak cap SHA-256 bagi RPT sumber dan menghasilkan RPT Word semakan bersama 69 RPH Word/PDF.
- **HOLD semakan guru.** Draf bebas dieksport untuk semakan. Pengesahan akademik dan ujian muat turun Web/Telegram masih diperlukan sebelum pelepasan.
