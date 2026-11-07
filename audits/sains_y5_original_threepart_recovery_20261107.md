# Bukti pemulihan sumber Buku Teks Sains Tahun 5 — tiga PDF asal

**Tarikh audit:** 7 November 2026. **Skop:** STAGING/HOLD, PR #442. Tiada kemas kini DB, tiada muat naik PDF buku teks berhak cipta ke GitHub, tiada pengesahan akademik automatik.

## Punca kelemahan rujukan Tahun 5

Fail Buku Teks Tahun 5 yang tersimpan dalam Drive projek, `GuruBesar_BukuTeks_Sains_T5_SK.pdf`, memang mempunyai **43 halaman PDF sahaja**, sehingga muka surat bercetak **35**. Hakikat ini kini dibezakan daripada keadaan buku penuh: **bukan buku Sains Tahun 5 yang hanya ada 35 halaman**, tetapi salinan projek yang hanya mengandungi **bahagian pertama**.

Saya menjejaki dua bahagian selebihnya daripada senarai sumber pendidikan awam [Bumi Gemilang — Buku Teks Sains Tahun 5](https://www.bumigemilang.com/buku-teks-digital-sains-kssr-tahun-5-2/) dan [PPD Batu Pahat — Sains Tahun 5](https://sites.google.com/moe-dl.edu.my/ppd-batu-pahat-sains-matematik/buku-teks-digital-bidang-sains-matematik/buku-teks-sekolah-rendah/sains-tahun-5). Fail yang dirujuk merupakan Buku Teks Sains SK (KSSR Semakan 2017), cetakan 2020, ISBN **978-983-49-2831-5** pada bahagian pertama.

| Bahagian | Pautan PDF asal | Julat halaman bercetak | Halaman PDF | SHA-256 |
|---|---|---|---:|---|
| 1 (Drive projek asal) | [Muat turun sumber](https://drive.google.com/file/d/1m5k8gVkNImT8QEdw6fCEVpQh_tNkUKUT/view) | 1–35, selain 8 halaman awal | 43 | `322b8ea0e19fc5b6da1c41ff64a25d22e470917027d9b293c85efc045a6be3e2` |
| 2 (sumber pendidikan) | [Muat turun sumber](https://drive.google.com/file/d/1xvpW8HgqrTdrl8QJCHUx0pDIiyuBLjIJ/view) | 36–130 | 95 | `7469fdadc20cfb275256e5d760f86b36f859cc259f31610865052d752acf820e` |
| 3 (sumber pendidikan) | [Muat turun sumber](https://drive.google.com/file/d/1YnwPPyyLoGCzP_m3izeB_PFn3w7XGsPt/view) | 131–234 | 104 | `629a17b3b493e121285cba65e0925023c71cefadd5c3a740f6e6b82b63ce3d9d` |

**Semakan fail fizikal:** Semua tiga PDF diambil dan dibuka menggunakan PyMuPDF. Semua **234 halaman bercetak 1–234** diliputi **tanpa jurang atau halaman berganda**. Peralihan p35→p36 dan p130→p131 diteliti; 16 halaman contoh (20, 28, 35, 36, 50, 74, 94, 118, 130, 131, 146, 164, 178, 200, 218, 234) dirender sebagai imej dan diperiksa secara visual.

## Padanan SP 83 RPH Tahun 5

- **83/83 kod SP** daripada 83 PdP Tahun 5 versi sumber staging ditemui secara **padanan token SP dalam teks PDF buku asal** pada sekurang-kurangnya satu halaman yang tepat.
- Ini merangkumi **103 halaman bercetak unik** yang mempunyai label satu atau lebih SP daripada 83 sumber.
- Setiap SP mempunyai satu atau lebih `printed_pages`, `primary_page` dan status sumber dalam `audits/sains_y5_83_full_textbook_printed_sp_pages_20261107.json`.
- Skrip `tools/sains_y5_83_textbook_original_sp_pages_20261107.py` menolak sumber jika checksum/julat/83 identiti/halaman atau status kelulusan berubah tanpa semakan.
- Penjana `tools/render_sains_y5_83_rph_draf_20261107.py` menggunakan **satu halaman rujukan primer yang disemak kod SP** dalam Word/PDF, senarai calon tambahan dalam Markdown/manifest, dengan **label pedagogi/PBD belum diluluskan panitia**.
- Senarai semakan panitia untuk 342 PdP di `tools/export_sains_342_panitia_review_20261107.py` turut menyertakan semua tiga sumber Tahun 5.

### Had bukti dan gerbang kelulusan

**Padanan kod SP pada satu halaman tidak membuktikan bahawa semua arahan atau latihan pada halaman itu sesuai untuk SP, KPS dan penilaian individu sebenar.** Semakan visual sistematik kandungan 83 PdP dan pengesahan guru/panitia masih terbuka; hanya 16 halaman contoh dirender/disemak semula selepas pemulihan sumber ini. Kod QA **tidak** melabel 83/83 sebagai lulus akademik dan tidak mencipta TP atau markah 80%.

Beberapa buku asal memaparkan aktiviti yang menggunakan bahan panas, alat tajam atau arus elektrik. Arahan RPH draf menggunakan alternatif selamat (gambar, model, sel kering, video guru) tetapi masih memerlukan penilaian kesesuaian dengan murid dan kemudahan sebenar.

**Tiada tiga PDF buku asal dimasukkan ke dalam artifak GitHub atau ZIP RPH.** Bahan asal mesti diperoleh melalui pautan sumber masing-masing mengikut hak cipta dan kebenaran penggunaan.

**Keputusan:** Sumber Buku Teks Tahun 5 lengkap untuk **pemeriksaan padanan halaman/kod SP 83/83**. Tahun 5 masih **DRAF/HOLD**, bukan READY.
