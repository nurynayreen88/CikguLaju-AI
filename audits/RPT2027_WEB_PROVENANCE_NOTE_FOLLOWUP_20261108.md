# RPT 2027 — Susulan audit teks dalaman pada Web

Tarikh: 8 November 2026. Skop: 56 PDF **Web** yang berada dalam katalog `rpt_2027/web_2027_pdfs/`. Semua angka di bawah merujuk kandungan sebelum pembetulan susulan ini, bukan bilangan pelajaran salah.

## Bukti kebocoran kedua dalam PDF yang sudah lulus audit pertama

| Jenis teks | Padanan pada PDF sedia ada | Tindakan paparan |
|---|---:|---|
| Nota `Main/Complementary codes from source SOW` (English) | 774 (771 ayat penuh, 3 separa) | Gugurkan arahan pembangun, kekalkan rujukan Student Book dan Lesson |
| `tidak mereka halaman buku teks` (Pendidikan Islam) | 106 | Buang arahan pembangun, kekalkan rujukan Mushaf/tasmi |
| `SCI-Yn-PDP-nnn` (Sains) | 342 | Cetak `PdP nnn`, simpan kod crosswalk dalam sumber |
| `BMn-Pnnn` (Bahasa Melayu) | 1,636 | Buang kod crosswalk di paparan tajuk dan catatan sahaja |
| `Semak judul aktiviti penuh` (BM) | 19 | Tahan catatan penyemak daripada dicetak |
| `BA asal belum disemak` (BM) | 1 | Tahan rujukan BA belum sah daripada dicetak sebagai fakta |
| `jangan dakwa kedua-duanya setara` (BM) | 1 | Kekalkan isu kod SP dalam sumber audit; jangan cetak arahan pembangun |
| `TIADA KOD SP RASMI DALAM RPT SUMBER` dan `BUKAN KOD SK RASMI` | 5 setiap satu | Papar `Aktiviti pilihan guru (tiada SK/SP rasmi)` dan jangan cipta kod kurikulum |
| `RPT sumber` dalam catatan BM/PI | 9 | Buang frasa rujukan pembangun sambil kekalkan kandungan berguna |

## Prinsip non-destructive
- Semua catatan asal, status HOLD, kod crosswalk dan metadata pembangunan kekal dalam sumber; penapis hanya berkuat kuasa semasa membina PDF untuk guru.
- Status 56 PDF kekal DRAF. SK/SP Bahasa Arab, sebahagian Pendidikan Islam dan padanan DSKP Sains masih memerlukan pengesahan akademik.
- Ujian pratayang sumber dan katalog Web mesti lulus semula, termasuk checksum setiap 56 fail, kedudukan medan muka depan, nombor PdP/Lesson, font Jawi/Arab dan audit frasa versi kedua.
- Tidak mengubah Telegram `main`, database, akaun pengguna, kuota percubaan atau bil.
- Jangan merge staging sehingga artifak QA dan ujian muat turun Web diperiksa. Tidak boleh menganggap status akademik FINAL READY hanya kerana kandungan bebas nota pembangun.
