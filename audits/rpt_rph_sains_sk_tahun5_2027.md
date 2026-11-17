# RPT dan RPH Sains SK Tahun 5 2027 sebelum UASA

[RPT dan indeks Web di commit sumber](https://github.com/nurynayreen88/CikguLaju-AI/tree/57aa5be4c9c0cc8511a545ee88dfb4423df50cb9) mempunyai 116 PdP bernombor. Set semakan mengekalkan turutan PdP 001–116, 10 unit dan padanan 95 SP. Kesemua kod sepadan dengan [DSKP Sains Tahun 5 KSSR Semakan 2017, BPK April 2019](https://anyflip.com/kmsiv/oqkz/basic/51-88). Tajuk diringkaskan mengikut fokus SP supaya setiap satu boleh dibaca penuh dalam RPT.

## Agihan 64 jam

RPT asal menyatakan urutan PdP. Agihan semakan memperuntukkan 104 sesi 30 minit dan 12 sesi sejam. Terdapat 35 minggu pengajaran dengan dua hingga empat PdP, berjumlah 90 atau 120 minit setiap minggu. Sesi sejam diperuntukkan antaranya untuk ujian buih, pembinaan model haiwan, litar, pemanasan, penyejukan dan pengaratan.

Kesemua 14 PdP yang berada pada M39–43 dalam RPT sumber dialihkan. PdP terakhir ialah M38, 17–21 Oktober untuk Kumpulan A dan 18–22 Oktober untuk Kumpulan B. M18 dikhaskan untuk pentaksiran pertengahan tahun. M06 dan M19 kekal tanpa PdP baharu, dan M39–44 tersedia untuk ulang kaji, UASA dan aktiviti sekolah. M10 Kumpulan A bermula pada 15 Mac selepas cuti tambahan. [Kalendar Akademik KPM 2027](https://www.moe.gov.my/surat-siaran-kpm-bil1-tahun-2027-kalendar-akademik).

## Padanan RPH dan buku teks

- 83 PdP kandungan menggunakan [bank Sains SK Tahun 5](../web/sains_y5_83_activity_bank_draf_20261107.py) dan [lejar 83 rujukan buku teks](../audits/sains_y5_83_full_textbook_printed_sp_pages_20261107.json). Edisi rujukan ialah [Buku Teks Sains Tahun 5 SK, DBP 2020](https://anyflip.com/mcde/rewa/basic/), ISBN 978-983-49-2831-5.
- 12 PdP teras Kemahiran Proses Sains mempunyai tugasan khusus. Kesemua 21 PdP pengukuhan mempunyai bahan dan evidens individu yang berbeza daripada sesi teras dengan kod SP yang sama.
- PdP 066 mengubah bilangan mentol, dengan rujukan m/s 125–126 dan 128. PdP 067 mengubah bilangan sel kering sambil mengekalkan susunan dan bilangan mentol dalam setiap perbandingan, dengan rujukan m/s 125–127. PdP 086 memulakan penyiasatan pengaratan dan PdP 087 menilai rekod susulan.
- Nombor 001–116 merujuk kepada urutan RPT ini. Salinan pangkalan data v25.68 dan tambahan Unit 1 menghasilkan 88 kumpulan PdP lama bagi 95 SP. Kod lama `ST5-PDP-084` hingga `ST5-PDP-088` merujuk Kemahiran Proses Sains. Nombor 084–088 bagi RPT 2027 merujuk Pengaratan. Set 2027 menggunakan `SK27-SCI-Y5-PDP-001` hingga `SK27-SCI-Y5-PDP-116`, dengan tiada pertindihan ID tepat dengan 88 kumpulan sumber lama tersebut.

## Eksport dan status

Jalankan `PYTHONDONTWRITEBYTECODE=1 python -m staging.sains.tahun5.eksport_2027 --output /tmp/Sains_SK_Tahun_5`. Penjana mengeksport RPT Word serta 116 RPH Word dan PDF. RPT Word dan PDF mempunyai 12 halaman A4 landskap. Semakan setempat membandingkan semua 116 nombor dan kod SP dengan RPT sumber dan mengesahkan tempoh, tarikh A/B, rujukan buku, fasa dan evidens PBD pada set semakan.

## Ujian laluan dalaman

- Klien Flask menggunakan laluan dalaman Web ke penjana Telegram dengan sumber semakan. Kesemua 10 unit dan 116 pilihan memadankan nombor PdP, tajuk, SK/SP, halaman buku, PBD dan butiran kelas dalam respons Word/PDF. Permintaan tanpa token, unit yang salah dan ID lama ditolak oleh laluan semakan.
- Kesemua 116 PDF dan 116 Word yang ditukar menggunakan LibreOffice muat satu halaman A4. Sebanyak 116 PDF tambahan dengan sampel refleksi 500 aksara juga kekal satu halaman.
- Ujian yang boleh dijalankan semula ialah `python -m unittest discover -s tests -p 'test_sains_sk_tahun5_2027_review_sequence.py'`. Penyesuai set 2027 hanya dimuatkan oleh ujian ini.

**HOLD semakan guru dan CI.** Ujian muat turun melalui akaun guru di Web dan Telegram produksi belum dijalankan. Guru perlu mengesahkan liputan SK/SP dan pelaksanaan setiap RPH dalam set 2027, termasuk amali dan pemerhatian susulan.
