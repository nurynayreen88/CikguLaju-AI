# Sains Tahun 3 — tiga SP tambahan dalam PdP berbilang SP

**Tarikh 7 November 2026. Status STAGING/HOLD — bukan bahan Buku Aktiviti rasmi KPM.**

## Isu yang ditemui semasa audit 342 PdP

Sumber PdP asal Tahun 3 mempunyai tiga rekod yang **memetakan dua SP dalam satu PdP**. Padanan Buku Aktiviti yang diperiksa secara visual hanya menyasarkan satu SP utama bagi setiap PdP. Kedua-dua SP dalam sumber perlu dikekalkan, bukan digugurkan atau seolah-olah mempunyai latihan buku yang sepadan.

| Kod PdP | SP utama dari Buku Aktiviti | SP tambahan daripada sumber | Keperluan SP tambahan |
|---|---|---|---|
| SCI-Y3-PDP-006 | 3.2.1 | **3.2.5** | Menjelaskan pemerhatian tentang kelas makanan melalui lakaran, TMK, tulisan atau lisan kreatif |
| SCI-Y3-PDP-010 | 3.3.1 | **3.3.3** | Membuat rumusan tentang makanan tercerna yang tidak diperlukan badan |
| SCI-Y3-PDP-011 | 3.3.2 | **3.3.4** | Menjelaskan pemerhatian tentang pencernaan melalui lakaran, TMK, tulisan atau lisan kreatif |

**Sumber DSKP:** Dokumen Standard Kurikulum dan Pentaksiran Sains Tahun 3 KSSR Semakan 2017 melalui salinan teks yang boleh dibaca pada https://fliphtml5.com/dhphy/tqdi/DSKP_SAINS_TAHUN_3/ . Kesesuaian pelaksanaan tetap perlu pengesahan guru/panitia.

**Sumber Buku Aktiviti Tahun 3:** https://drive.google.com/file/d/1kVL3PT-VjQiITqmfNXlURQA8gLYvCrI5/view . Halaman dipadankan bagi SP utama sahaja dan **tidak didakwa membuktikan penguasaan SP tambahan**.

## Tindakan staging

- `tools/render_sains_y3_3_secondary_sp_pbd_20261107.py` menjana tiga lembaran PBD **asli CikguLaju**, masing-masing satu Word dan satu PDF A4, bertajuk kelas makanan, sisa pencernaan, serta penerangan proses pencernaan.
- Setiap lembaran mempunyai tiga aktiviti/tugasan individu, ruang jawapan, tiga kriteria guru dan peringatan keselamatan. **Tidak boleh dijual atau dipaparkan sebagai halaman Buku Aktiviti rasmi KPM**.
- `tools/render_sains_y3_45_review_pack_20261106.py` menambah **pautan nama lembaran asli** kepada tiga RPH Year3 yang berkaitan dalam bahagian PBD. PdP, SP utama, dan Buku Aktiviti asal dikekalkan.
- `tools/export_sains_342_panitia_review_20261107.py` memeriksa tiga lembaran PDF A4 benar-benar wujud sebelum mengeksport 342 baris semakan manual, lalu mencatat tiga SP tambahan secara eksplisit. Semua markah dan keputusan guru masih kosong/HOLD.
- Ujian GitHub `tests/test_sains_y3_3_secondary_sp_pbd_20261107.py` menyemak identiti 3 PdP dan kod SP serta kriteria tugasan, kemudian CI mencetak tiga PDF sebenar.

## Batas akademik

Ini menyelesaikan jurang **bahan penilaian contoh untuk tiga SP tambahan** secara editorial, **bukan pengesahan kualiti 80%**. Guru/panitia perlu menilai penjelasan, penentuan TP/PBD sebenar, kesesuaian tahap murid, sumber Buku Teks, dan kelulusan pengaktifan Web–Telegram. Terdapat **342 draf RPH Sains secara teknikal**, tetapi **0 kelulusan akademik automatik**.

**Jangan merge PR #442 atau deploy produksi sebelum pihak yang berwenang meluluskan bahan.**
