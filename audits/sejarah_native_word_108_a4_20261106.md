# Sejarah 2027 — pembaikan 108 RPH Word natif menjadi satu A4

Tarikh QA: 6 November 2026. Branch: `staging/sejarah-rpt-rph-y4-y6-2027-20261105`; [PR #341](https://github.com/nurynayreen88/CikguLaju-AI/pull/341).

## Penemuan sebenar

- Pratonton Word Sejarah yang dibina oleh penjana berasingan pernah mencatat 108/108 satu A4. Itu **tidak** membuktikan format natif Telegram.
- Ujian baharu melalui fungsi Word tiga-jadual yang padan AST dengan penjana aktif Telegram mendapati hanya **62/108** satu A4; **46/108** ialah **dua halaman** sebelum pemadatan. Bukti: [Actions run 42137930056](https://github.com/nurynayreen88/CikguLaju-AI/actions/runs/42137930056).
- Fungsi `web/sejarah_2027_word_compact.py` hanya mengubah **tataletak dokumen Sejarah**, dengan lebar lajur aktiviti lebih luas, padding sel lebih kecil dan font jadual 7.9 pt. Ia memeriksa teks XML asal dan akhir agar satu huruf pun tidak gugur.
- Laluan natif Web ke Telegram menggunakan pemadatan tersebut **hanya** jika subjek `SEJARAH`; subjek lain kekal pada kod terdahulu.
- Ujian semula menggunakan semua 108 RPH, penjana jadual Word yang sama dan LibreOffice -> **108/108 satu halaman A4, 0 kegagalan**, [Actions run 42138698755](https://github.com/nurynayreen88/CikguLaju-AI/actions/runs/42138698755). Artifak QA mengandungi manifest dan sampel Word/PDF untuk Tahun 4–6.
- Tiga QA sedia ada juga lulus pada commit `b836113924091d52b1093035e9eb1b498b9fadcf`: struktur + kawalan pengesahan, PDF RPH/RPT, pratonton Word.

## Had pengesahan

Ini semakan tataletak bagi fungsi natif Word melalui *snapshot* kod dengan padanan AST dan penukaran LibreOffice, bukan ujian mesej sebenar dalam Telegram atau penghantaran pengguna Web. **Belum** mengesahkan penjana PDF natif pada akaun pengguna sebenar, suntikan profil/logo sekolah, kehadiran nama kelas, guru, masa sebenar, atau kelulusan manusia.

Semua 108 RPH masih DRAF dalam sumber / manifest kelulusan bebas. **0/108** mempunyai pengesahan visual latihan buku teks dan tandatangan pedagogi guru. Kelulusan produksi **tidak** diubah dan `main` tidak disentuh.
