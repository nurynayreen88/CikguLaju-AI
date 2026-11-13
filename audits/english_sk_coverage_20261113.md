# Semakan English SK Tahun 1–6

Skop bahan English semasa ialah Sekolah Kebangsaan. Katalog SOW SK menjadi asas identiti Lesson. Untuk peluasan kemudian, tentukan jenis sekolah daripada rekod direktori yang dipadankan kepada kod sekolah. Simpan SK, SJKC dan SJKT sebagai nilai berasingan. Padankan bahan mengikut jenis sekolah, edisi kurikulum, tahun, subjek dan identiti Lesson. Apabila KPM menetapkan sumber SJK yang sama, kedua-dua jenis sekolah boleh merujuk dokumen tersebut melalui padanan yang disahkan. Rekod jenis sekolah yang belum dikenal pasti perlu disemak.

| Tahun | Katalog RPH Web | Buku Aktiviti boleh dipetik | Sambungan bahan lain |
| --- | --- | --- | --- |
| 1 | 2 Lesson KSSR Semakan 2017 dalam katalog semasa | Belum disambung pada laluan ini | Inventori lama mempunyai 158/160 fail dengan nama standard. KP2027 memerlukan semakan sumber berasingan. |
| 2 | 160 Lesson, 160 padanan standard tetap | 61 Lesson | Student Book Super Minds 1 First Edition boleh dipetik bagi 61 Lesson. Pemetaan audio Web meliputi 45 padanan trek WMA asal bagi 32 Lesson selepas audit sambungan. Lihat status pelepasan dalam log. |
| 3 | 160 Lesson, 160 padanan standard tetap | 70 Lesson | Student Book dan audio mengikut sumber Telegram. |
| 4 | 160 Lesson, 150 padanan tetap dan 10 pilihan guru | 107 Lesson | Petikan SB Lesson 43, 103 dan 157 dipadankan ke muka surat 121, 73 dan 110–111. Sekatan audio sedia ada masih berkuat kuasa. |
| 5 | 160 Lesson, 151 padanan tetap dan 9 pilihan guru | 130 Lesson | Student Book dan audio memerlukan semakan sumber dan laluan penghantaran. |
| 6 | 160 Lesson, 146 padanan tetap dan 14 pilihan guru | 111 Lesson | Student/Pupil's Book dan audio memerlukan semakan sumber dan laluan penghantaran. |

Kiraan Buku Aktiviti ialah petikan 1–4 halaman yang berjaya dijana daripada fail PDF asal repositori. Lesson tanpa padanan atau yang melebihi had empat halaman belum dipaparkan. Bilangan dalam katalog mengukur liputan rekod, manakala akses RPH sebenar mengikut kelulusan dan laluan janaan setiap Lesson. Katalog RPT Web menyediakan pilihan English Tahun 2–6 dan menanda Tahun 1 KP2027 belum dibuka.

Audit sumber teknikal menjalankan semula `tools/audit_english_800_text_quality_20261104.py --strict`. Kesemua 767 pasangan standard tetap Tahun 2–6 sepadan. Penerbitan individu RPH, pilihan guru, semakan fizikal buku dan trek serta muat turun dengan akaun guru produksi perlu dibuktikan mengikut keluaran.

## Semakan tambahan English Tahun 2

Semua 61 padanan halaman BOT_READY dalam pangkalan data asal dan versi v15 adalah sama. Versi v15 mempunyai 53 Lesson yang ditanda mempunyai audio disahkan. Semakan halaman buku asal dan ID penghantar Telegram mengesahkan enam trek untuk Web.

| Lesson | Muka surat Student Book | Trek asal |
| --- | --- | --- |
| 2 | 58 | CD2 Track 18 dan 19 |
| 26 | 70 | CD2 Track 35 dan 36 |
| 88 | 94 | CD3 Track 17 dan 18 |

Enam fail asal dapat diambil dan dikenal pasti sebagai WMA. Kedua-dua trek Lesson 26 turut sepadan dengan SHA256 audit terdahulu. Ujian setempat dengan sesi guru ujian menggunakan PDF sebenar dan fail WMA asal untuk ketiga-tiga Lesson. Muat turun dengan sesi guru produksi belum diuji.

Baki 50 daripada 53 rekod audio v15 memerlukan semakan halaman atau Teacher's Book dan fail asal sebelum disenaraikan di Web. Contohnya, buku muka surat 98 mencetak CD3 Track 26 bagi cerita, manakala rekod lama Lesson 98 menyenaraikan CD3 Track 27. Buku muka surat 106 mencetak CD3 Track 34 dan 35, manakala rekod lama Lesson 126 menyenaraikan CD3 Track 37 dan 38. Sumber dan laluan penghantaran asal Telegram dikekalkan.


## Sambungan audit audio English Tahun 2 SK

Semakan baki 50 rekod v15 mendapati 21 Lesson lagi dengan 24 trek yang sepadan dengan halaman dan aktiviti dalam Super Minds 1 First Edition. Setiap ID diambil daripada penghantar WMA Telegram. Fail asal dimuat turun dan disahkan melalui tandatangan ASF, codec WMA, nombor trek terbenam dan nyahkod penuh. Semakan ini tidak mengubah data v15, fail sumber atau laluan Telegram.

| CD | Lesson dan muka surat Student Book |
| --- | --- |
| 2 | 4 (60), 11 (61), 14 (64), 21 (66), 23 (68), 31 (71), 32 (73), 33 (74–75), 35 (72), 41 (75), 43 (77), 51 (80) |
| 3 | 57 (83), 67 (85), 77 (89), 78 (90), 86 (92), 89 (95), 107 (100), 109 (102), 129 (109) |

**HOLD bagi 29 Lesson:** 3, 12, 13, 20, 42, 56, 66, 68, 71, 79, 87, 96–98, 106, 108, 116–119, 126–128, 136–139, 146 dan 147. Sebahagian rujukan tidak dicetak pada halaman Student Book yang dipadankan. Contohnya, Lesson 96 merujuk CD3 Track 20 dalam v15, sementara m/s 96 mencetak Track 21 dan 23. Sesetengah nombor mungkin berasal daripada Workbook atau panduan guru. Semak aktiviti dan trek pada bahan itu sebelum pelepasan. Tiada pembetulan automatik pada padanan Telegram.

Jumlah selepas perubahan ialah 24 daripada 53 Lesson bertanda VERIFIED_AUDIO dalam v15. Ujian muat turun menggunakan sesi guru produksi belum dibuat.


## 14 November 2026 — Semakan Teacher’s Book dan Workbook Tahun 2 SK

Silang semak Primary Year 2 SK Scheme of Work dengan *Super Minds 1* edisi pertama, Teacher’s Book T96–T112, halaman bercetak Student Book dan Workbook, serta baris sebenar v15. Trek disenaraikan mengikut aktiviti yang sepadan. Buku dan fail WMA asal kekal pada sumber sedia ada.

| Lesson | SOW m/s | Student Book dan CD3 | Workbook dan CD3 |
| --- | --- | --- | --- |
| 96 | 219 | m/s 96, Aktiviti 1 dan 2, Track 21 dan 23 | m/s 96, Aktiviti 1 padanan gambar dan ayat |
| 97 | 221 | m/s 97, Aktiviti 1 dan 2, Track 24 dan 25 | m/s 97, Aktiviti 1 dan 2 latihan soalan dan jawapan |
| 98 | 223 | m/s 98–99, Aktiviti 1, Track 26 | m/s 98, Aktiviti 1, Track 27 |
| 106 | 239 | m/s 99, Aktiviti 4, Track 28 | m/s 99, Aktiviti 2, Track 29 |
| 108 | 243 | m/s 101, bacaan dan penulisan | m/s 101, Aktiviti 1, Track 31 |
| 136 | 299 | m/s 110–111, Aktiviti 1, Track 43 | m/s 110, Aktiviti 1, Track 44 |
| 137 | 301 | m/s 111, Aktiviti 4, Track 45 | m/s 111, Aktiviti 2, Track 46 |
| 138 | 303 | m/s 112, Aktiviti 2, Track 47 | m/s 112, Aktiviti 1, Track 48 |

Teacher’s Book T95 mengesahkan bahawa Track 20 digunakan pada Student Book m/s 95, Aktiviti 3. Track 21 ialah lagu m/s 96, jadi rujukan lama Lesson 97 juga tersasar. Lesson 139 dan 146 kekal HOLD kerana rujukan v15 menggunakan trek yang telah dikenal pasti pada bahan Lesson 138. Aktiviti pada halaman bercetak Lesson 139 dan 146 memerlukan semakan berasingan.

ID 15 trek sepadan dengan katalog penghantar Telegram asal. Semua fail lulus semakan pengepala ASF, codec WMAv2, nombor trek terbenam dan nyahkod penuh. Laluan Web memeriksa identiti Lesson, halaman Student Book dan Workbook serta rujukan v15 sebelum menyenaraikan fail dengan label buku, halaman dan aktiviti. Penambahan ini dibuat pada laluan bahan Web, sementara Telegram terus menggunakan pemetaan penghantaran asal mengikut arahan pemilik projek.

Baki **21 Lesson HOLD** ialah 3, 12, 13, 20, 42, 56, 66, 68, 71, 79, 87, 116–119, 126–128, 139, 146 dan 147. Muat turun menggunakan akaun guru produksi belum disahkan.
