# SAINS TAHUN 2 — Semakan isi DSKP Unit 3 & 10.1.6 (7 Nov 2026)

**Status: STAGING / HOLD.** PR #442. Tiada merge/deploy, tiada pertukaran DB, tiada pengubahan 51 Kod PdP sumber Tahun 2.

## Bukti daripada DSKP sebenar

Sumber asal KPM: https://drive.google.com/file/d/1rr4CjNvhtI13ioiVSTZi65cvap7j1U6Z/view

| Kod SP DSKP | Teks DSKP (yang relevan) | Status sumber CikguLaju |
|---|---|---|
| 3.1.3 | Mengitlak tumbesaran adalah berbeza antara individu dengan menjalankan aktiviti. | Dalam PdP003, tetapi tajuk warisan pada sumber legasi salah; tajuk pembetulan kekal DRAF |
| 3.1.4 | Memerihalkan bahawa anak mewarisi ciri daripada ibu, bapa atau keturunan. | Tiada PdP tersendiri antara 51 sumber |
| 3.1.5 | Memberi contoh ciri yang diwarisi oleh anak daripada ibu bapa atau keturunan seperti warna kulit, warna mata dan jenis rambut. | Tiada PdP tersendiri antara 51 sumber |
| 3.1.6 | Menjelaskan pemerhatian tentang tumbesaran dan pewarisan melalui lakaran, TMK, penulisan atau lisan. | Tiada PdP tersendiri antara 51 sumber |
| 10.1.6 | Menjelaskan pemerhatian tentang **campuran** melalui lakaran, TMK, penulisan atau lisan. | DSKP tercetak **campuran** di bawah Unit 10 Set Binaan; teks rasmi tidak boleh dipalsukan kepada 'binaan'. PdP051 kekal DRAF/HOLD |

Tiga SP 3.1.4–3.1.6 merupakan jurang **pemetaan kandungan DSKP kepada PdP**, bukan bukti bahawa tiada pengajaran langsung berlaku dalam RPT mana-mana sekolah. RPH tambahan disediakan **tanpa mencipta identiti PdP rasmi**, dan tidak diselitkan secara senyap ke sumber asal Tahun 2.

## Tindakan staging yang dilaksanakan

- `audits/sains_y2_unit3_unmapped_sp_semantic_20261107.json`: bukti teks DSKP asal, tiga SP tercicir, dua percanggahan sumber serta syarat kelulusan. Status sentiasa **HOLD**.
- `tools/render_sains_y2_3_unmapped_sp_pbd_20261107.py`: tiga lembaran **PBD sokongan asli CikguLaju**, satu untuk SP3.1.4, SP3.1.5 dan SP3.1.6 (Word + PDF satu halaman A4). Setiap satu mempunyai tugasan individu, ruang jawapan, kriteria dan keselamatan/privasi. **BUKAN PdP baharu / BUKAN BUKU AKTIVITI KPM.**
- `tools/render_sains_y2_51_rph_draf_20261107.py`: dua amaran sumber secara nyata pada RPH PdP003 dan PdP051 dalam Word/PDF; tidak menyunting SP sebenar atau mencipta nombor halaman Buku Teks.
- `tools/export_sains_342_panitia_review_20261107.py`: CSV panitia **342 PdP asal** ditambah **CSV berasingan untuk 3 SP belum berjadual**. Ini mengelakkan statistik 342 menjadi 345 yang tidak benar.
- `tests/test_sains_y2_unit3_missing_sp_20261107.py` dan `tools/check_sains_342_rph_format_20261107.py`: cegah SP atau bahan sokongan dianggap telah diluluskan, serta uji amaran DSKP tercetak benar-benar muncul dalam RPH Word/PDF.

## Keputusan akademik yang masih diperlukan

1. Guru/panitia perlu tentukan **penempatan 3 SP** dalam RPT yang disahkan, termasuk sama ada digabungkan dalam beberapa PdP Unit 3; jangan menaikkan nombor PdP rasmi berdasarkan andaian.
2. Semak kesesuaian lembaran pewarisan dengan usia murid, sensitiviti data keluarga dan keberkesanan bukti PBD. Semua watak, ukuran dan keluarga dalam bahan ialah contoh **rekaan**, tiada maklumat murid sebenar.
3. Semak SP10.1.6 dalam versi DSKP/cetakan rasmi dan buku teks. Jika dokumen rasmi mempunyai pembetulan kemudian, rekodkan bukti versi; **jangan ubah teks KPM secara senyap**.
4. Semak halaman Buku Teks Tahun 2 pada imej asal, bukannya hanya petunjuk lapisan teks PDF.
5. Jalankan ujian Web–Telegram **staging** menggunakan sumber DB sama. Tiada bahan ini diaktifkan kepada pengguna.

**Status selepas kerja ini: 342 draf RPH sedia untuk semakan guru, ditambah 3 dokumen sokongan SP Unit 3 yang belum berjadual; akademik 0 diluluskan; tiada promosi READY atau 80%.**
