# RBT CikguLaju Tahun 4–6 · DRAF 2027
**STAGING SAHAJA — BELUM FINAL READY. TIDAK DIINTEGRASI KE TELEGRAM/WEB, TIADA DEPLOY.**

## Isi kerja
- 3 RPT 2027 CSV + 3 set RPH JSON asli untuk **96 PdP cadangan**: 32 PdP x 60 minit setiap tahun.
- RPH mempunyai langkah set induksi (5 minit), aktiviti 1 (15 minit), aktiviti 2 (25 minit), penilaian (10 minit) dan penutup (5 minit), bahan PdP, objektif, PBD dan keselamatan.
- Kod SP yang terdapat dalam DSKP dipadankan: Tahun 4 = 57 kod; Tahun 5 = 34 kod; Tahun 6 = 23 kod. **Jumlah kod unik 114**. Satu SP boleh diajar dalam lebih satu sesi untuk projek/amali.
- Semua 96 RPH kini mempunyai aktiviti berfokus SK/SP, projek cadangan khusus bidang, artefak dan rubrik PBD yang berbeza mengikut unit. **Ini bukan perakuan mutu pedagogi secara individu**.
- 32 jam ialah peruntukan minimum setahun dalam DSKP; `32 PdP x 60 minit` bukan jadual PdP rasmi KPM. Masa kelas sebenar boleh dipecahkan dalam jadual guru.

## Peruntukan DSKP
| Tahun | Modul | Jam |
|---|---|---:|
| 4 | Keselamatan Bengkel; Pengenalan Reka Bentuk; Pengenalan Teknologi; Pembungkusan; Makanan; Pengaturcaraan | 3+7+4+5+5+8 = 32 |
| 5 | Artikel Jahitan; Tenaga Boleh Baharu; Asas Pengaturcaraan; Mikropengawal; Pertanian Bandar | 6+6+4+8+8 = 32 |
| 6 | Elektromekanikal; Robotik; Pembangunan Produk | 10+10+12 = 32 |

## Sumber dan kekangan
- DSKP KSSR (Semakan 2017) RBT Tahun 4, 5, 6 dalam folder **Reka Bentuk dan Teknologi** Google Drive pemilik.
- Buku teks Tahun 4 dalam folder yang sama. Padanan kod SP ke halaman bercetak telah dibuat untuk **57/57 SP dan 32/32 PdP** melalui teks PDF. Calon halaman disimpan dalam setiap RPH dan `audits/rbt_t4_textbook_sp_page_map_20261106.json`. Ini **belum kelulusan visual aktiviti atau guru**.
- Buku teks Tahun 5–6 belum ditemui dalam folder RBT Drive. Pautan awam telah dikenal pasti, tetapi halaman dan aktiviti belum dipadankan. Tahun 6 **wajib guna edisi KSSR Semakan 2017 cetakan 2021 (ISBN 978-983-49-3283-1)**, bukan buku lama ber-ISBN 978-983-49-0275-9 (2015).
- RPT 2026 awam wujud; belum dimasukkan sebagai sumber penjadualan terverifikasi.
- Pemetaan tema/Unit/PdP adalah editorial CikguLaju. Kumpulan A/B tarikh dan cuti negeri dibiarkan kosong untuk mengelak tarikh palsu.

## Semakan wajib sebelum pengguna boleh akses
1. Semak setiap RPH secara individu dengan aktiviti DSKP, buku teks Tahun 4–6 (terutama halaman dicetak), alatan tersedia dan keselamatan murid.
2. Perhalusi aktiviti khusus guru/murid untuk mencapai standard; pastikan bukan aktiviti templat semata-mata.
3. Uji Word/PDF natif: setiap RPH satu halaman A4, RPT landscape + muka depan Kumpulan A/B.
4. Semak jadual 2027, cuti negeri, pengurusan projek amali dan jadual waktu kelas.
5. Semak eksport dan padanan sumber yang sama pada Telegram & Web, tanpa mengubah kelas, bayaran, menu atau database produksi.
6. Kelulusan manual **per PdP**. DRAF mesti kekal dikunci sehingga semua syarat di atas lulus.

Semak data: `python scripts/check_rbt_t4_t6_2027.py`.

## Pemurnian 6 November 2026
- 96/96 langkah RPH telah dikhususkan kepada tugasan reka bentuk, penghasilan produk, kemahiran dan penilaian projek mengikut bidang; bukan ayat generik yang sama untuk semua subjek.
- Semua bahan kekal DRAF; 0 kelulusan guru, 0 pengujian penjana natif Word/PDF, 0 pengaktifan pengguna.
- Sumber awam rujukan edisi Tahun 6: https://fliphtml5.com/rjdzf/cwso/basic (cetakan pertama 2021, ISBN 978-983-49-3283-1). RPT 2026 sumber silang: https://sites.google.com/moe-dl.edu.my/teduristopcenter/kurikulum/pengurusan-panitia/panitia-reka-bentuk-teknologi ; rujukan belum disahkan secara baris demi baris.


## Audit minggu/tarikh selepas pembetulan RPT 2027 (7 November 2026)

- PDF RBT Tahun 4, 5 dan 6 kini menggunakan format lima lajur dengan kod dan pernyataan penuh SK/SP dan muka depan minimum (logo sekolah, nama sekolah, nama guru), tetapi **96/96 PdP masih tiada alokasi minggu dan tarikh Kumpulan A/B dalam sumber CSV**.
- Kalendar induk 2027 CikguLaju mempunyai 44 minggu berjadual bagi setiap kumpulan. **Peruntukan 32 jam setahun RBT bukan bukti bahawa PdP 001 mesti diletakkan pada M01 atau satu PdP/minggu**; pengagihan mengikut jadual sekolah/guru dan masa projek.
- Sumber perbandingan RPT 2026 telah dikenal pasti pada laman sekolah (rujukan **sejarah susunan SK/SP, bukan salinan tarikh atau minggu 2027**):
  - https://sites.google.com/moe-dl.edu.my/teduristopcenter/kurikulum/pengurusan-panitia/panitia-reka-bentuk-teknologi — RPT Tahun 4, 5 dan 6 2026 (.docx)
  - https://sites.google.com/moe-dl.edu.my/sjkcminsin/kurikulum/panitia-reka-bentuk-teknologi — RPT Tahun 4–6 2026 (.pdf)
  - https://sites.google.com/moe-dl.edu.my/panitia-tmk-rbt-skepa/dskprpt — dokumen RPT Tahun 4–6 (tahun/cetakan perlu disahkan)
- Langkah pengesahan: padan urutan setiap PdP dengan DSKP dan RPT 2026, kemudian masukkan minggu 2027 **hanya apabila** ada jadual kelas sebenar atau agihan sekolah yang boleh dijejak; validasi hari PdP sebenar menggunakan indeks negeri KPM/BKPP. Kumpulan A/B boleh berbeza dan tidak boleh disamakan tanpa bukti.
- Penjana staging tidak mengubah rekod pengguna atau menampal tarikh anggaran, dan status terus **DRAF / BLOCKED**.
