# RPT dan RPH Mathematics DLP Year 6 SK 2027

Set semakan guru mengandungi 46 Lesson dan lapan Review dalam lapan unit, berjumlah 5,760 minit atau 96 jam. Turutan, tarikh Kumpulan A/B, tempoh, CS/LS dan fokus PBD mengikut [RPT Year 6 semasa](../rpt_2027/dlp/CikguLaju_RPT_DLP_2027_Mathematics_Year_6.docx), diselaraskan dalam [PR #909](https://github.com/nurynayreen88/CikguLaju-AI/pull/909). Sesi terakhir ialah ulang kaji pada Minggu 38.

Kesemua 38 kod LS sepadan dengan DSKP KSSR Semakan 2017 edisi Inggeris Januari 2022 [bahagian awal](https://anyflip.com/vuzl/tmnx/basic/) dan [bahagian akhir](https://anyflip.com/vuzl/tmnx/basic/51-80). Padanan halaman menggunakan cetakan [Mathematics Year 6 BT086001, DBP 2021](https://fliphtml5.com/snttz/gmou/Mathematics_DLP_Year_6/), ISBN 978-983-49-3328-9, seperti dalam [E-Katalog KPM](https://moe.gov.my/storage/files/shares/Banner/E-Katalog%20Buku%20Teks%20KPM.pdf).

## Padanan rujukan dan aktiviti

- Lima rujukan buku diselaraskan pada kedua-dua draf. Lesson 12 meliputi latihan bahagi pecahan hingga hlm. 67. Lesson 23 menggunakan hlm. 116–120 untuk pulangan, aset dan liabiliti. Lesson 26 menggunakan hlm. 121–122 untuk insurans dan takaful. Review Unit 3 merujuk hlm. 114 dan 133–136 untuk resit serta latihan wang. Review Unit 8 merujuk hlm. 223–224 bagi carta dan kebolehjadian.
- Terdapat satu sesi 30 minit, 12 sesi 60 minit, 19 sesi 90 minit dan 22 sesi 150 minit. Semua RPH mempunyai tindakan guru dan murid, tugasan individu serta contoh jawapan PBD. Sesi 150 minit memperuntukkan fasa berasingan untuk demonstrasi dan aplikasi berpandu. Review menggunakan kod LS yang telah diajar dalam unit.
- Lesson 29–30 menggunakan zon masa yang dinyatakan dalam soalan, termasuk perubahan hari. Lesson 39 menggunakan skala untuk mengira jarak mengufuk dan mencancang. Lesson 43 menilai sektor 45°, 90° dan 180°, dan Lesson 44–46 membezakan kebolehjadian daripada keputusan satu percubaan.

## Semakan PBD selepas eksport awal

- Lesson 13 dan 19 menyertakan contoh anggaran, jawapan tepat dan langkah operasi yang diminta.
- Lesson 26 menilai model perkongsian risiko takaful dan tanggungan risiko insurans, di samping pemadanan perlindungan dengan situasi. Rujukan kekal m/s 121–122.
- Review 03 menilai keputusan belian berdasarkan resit dan bajet. Lesson 36 menyatakan kedudukan semua titik pada lilitan supaya murid boleh menentukan jejari dan diameter.

## Pengesahan dan eksport

- Kesemua 54 baris sepadan antara draf RPT dan RPH pada urutan, tempoh, tarikh A/B, standard, rujukan buku dan fokus PBD. Semua 54 RPH Word yang dirender dan 54 PDF asli muat satu halaman A4. RPT semakan dirender sebagai tujuh halaman A4 landskap.
- Jalankan `PYTHONPATH=. python -m staging.dlp.year6.render_mathematics --output /tmp/rph-dlp-y6` untuk menyemak RPT sumber dan mengeksport RPT Word semakan serta kesemua 54 RPH dalam Word dan PDF.
- Ujian eksport dalam CI menyemak 54 Word, 54 PDF, jadual RPT semakan dan lima rujukan halaman yang berubah. Semakan setempat melalui LibreOffice turut mengesahkan satu halaman A4 bagi setiap Word.
- **HOLD semakan guru.** Draf tersedia untuk semakan. Penerbitan di Web dan Telegram menunggu pengesahan akademik, CI dan ujian muat turun pengguna.
