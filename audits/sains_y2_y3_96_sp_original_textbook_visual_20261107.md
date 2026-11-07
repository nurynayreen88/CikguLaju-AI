# Sains Tahun 2–3 — semakan imej halaman Buku Teks KPM asal (7 November 2026)

**STAGING/HOLD**. Tiada perubahan DB, akaun, kuota, Telegram/Web produksi, markah akademik atau status READY.

## Sumber asal yang diperiksa

| Buku Teks | Fail asal daripada Drive | SHA256 PDF | Bil. halaman PDF |
|---|---|---|---:|
| Sains Tahun 2 SK (2017) | [Google Drive](https://drive.google.com/file/d/1LkJJWUb-zyFJ1ftpHM-4HIpIcEGLORI9/view) | `cf2e00ba3fc77290dd4298d563faf7e0b352343301120ecf962b735f342d366b` | 136 |
| Sains Tahun 3 SK (2018) | [Google Drive](https://drive.google.com/file/d/17QNqKZjSF7V9GzzkXkz46bDJGnyKYq-F/view) | `5c5c95276915abfc52dab3515040064502cf10e8fcc4e1682648b9ee260f1cb8` | 147 |

Kedua-dua PDF telah diambil terus daripada sumber Google Drive yang dipilih. Semua halaman berkenaan dirender sebagai imej dan diperiksa, selain padanan teks SP dan nombor halaman PDF sebenar. **Imej/fail PDF asal tidak dimasukkan semula ke repositori kerana buku berhak cipta; pautan sumber dikekalkan.**

## Keputusan teknikal sumber

| Ukuran | Tahun 2 | Tahun 3 |
|---|---:|---:|
| Rekod PdP sumber asal | 51 | 45 |
| Kod SP yang ditemui pada sekurang-kurangnya satu halaman Buku Teks bercetak yang dirujuk | **51/51** | **45/45** |
| Halaman bercetak unik yang diperiksa visual | **43** | **54** |
| Offset PDF *indeks bermula sifar* berbanding m/s bercetak | +5 | +7 |
| Kelulusan kesesuaian pedagogi/pentaksiran oleh guru/panitia | **0** | **0** |

Bukti rinci (setiap SP, m/s bercetak, indeks PDF, status pemerhatian imej dan status akademik):
- `audits/sains_y2_51_textbook_original_page_visual_20261107.json`
- `audits/sains_y3_45_textbook_original_page_visual_20261107.json`

Ini **mengesahkan rujukan kod SP pada halaman Buku Teks asal**, bukan kesesuaian semua arahan RPH, aktiviti sebenar, tuntutan TP atau penyataan lengkap DSKP. Halaman berbilang rujukan mempunyai sekurang-kurangnya satu label SP yang sepadan, bukannya semua halaman mempunyai label tersebut.

## Penemuan khusus

**Tahun 2**
- SP **3.1.3** dalam Buku Teks **m/s 28** mengenai tumbesaran berbeza antara murid, bukan pewarisan. Tajuk salah pada sumber legasi telah ditandakan untuk semakan.
- SP **3.1.4, 3.1.5, 3.1.6** juga benar-benar terdapat dalam buku asal tetapi tidak mendapat PdP tersendiri daripada 51 rekod lama. Buku Teks m/s **30, 32, 33**, Buku Aktiviti m/s **17–20** mempunyai label SP berkaitan. Tiga lembaran PBD sokongan disediakan **tanpa mencipta nombor PdP rasmi**; guru/panitia mesti memutuskan di mana SP digabungkan dalam RPT.
- SP **10.1.6** muncul pada Buku Teks **m/s 124** bersama aktiviti set binaan. **DSKP asal masih mencetak “campuran”** dalam SP10.1.6. Ini ialah percanggahan dokumen rasmi yang belum diluluskan untuk diperbetulkan; teks asal tidak diubah dan RPH PdP051 mempunyai amaran jelas.

**Tahun 3**
- **45 kod SP** mempunyai bukti halaman Buku Teks asal, termasuk **10.1.4 pada m/s 133** yang pernah dilabel berdasarkan petunjuk isi kandungan sahaja.
- Tiga SP tambahan dalam PdP berbilang-SP sudah terdapat dalam sumber Buku Teks: **3.2.5 (m/s 41)**, **3.3.3 (m/s 52)** dan **3.3.4 (m/s 51, 54)**. Lembaran PBD tambahan asli disimpan berasingan, bukan dianggap halaman Buku Aktiviti rasmi.
- Buku Teks Sains Tahun 3 **m/s 109–110** mengandungi gambaran rasa/sentuh bahan berasid atau beralkali. Panduan keselamatan RPH memilih data litmus/gambar dan melarang murid merasa bahan ujian.

## Perubahan pada kod staging

- Penjana RPH Tahun 2 membaca ledger bukti visual 51 halaman; menggunakan rujukan m/s yang diperiksa dan tetap mencetak **“isi/PBD belum disahkan panitia”**.
- Penjana RPH Tahun 3 juga membaca ledger 45 asal; m/s dan label SP yang diperiksa dibezakan daripada kelulusan kandungan.
- `tools/export_sains_342_panitia_review_20261107.py` memberikan pautan dan status buku Tahun 2–3 kepada senarai semakan **342 PdP asal**. Tiga SP tambahan Tahun 2 berada dalam jadual **berasingan**, tidak menjadi PdP ke-343 hingga ke-345.
- CI mengesahkan bahan dan QA satu halaman A4; ujian tidak boleh menaikkan status READY berdasarkan bukti halaman buku sahaja.

## Baki syarat sebenar

1. **Guru/panitia** perlu mengesahkan makna SP, kesesuaian setiap aktiviti dan tugasan PBD individu, penilaian keselamatan, serta menyelesaikan isu sumber DSKP.
2. Semak sumber Buku Teks Tahun 4–6 secara visual pada muka surat SP sebenar (bukan hanya TOC).
3. Sahkan sesi PdP/RPT Kumpulan A/B, cuti negeri/gantian dan jadual waktu guru.
4. Uji bahan melalui akaun staging **Web & Telegram menggunakan DB yang sama**, termasuk muat turun Word/PDF, akses pengguna dan fail buku.
5. Hanya selepas semua bukti akademik dan integrasi lengkap, skor ≥80% boleh dinilai dan keputusan penerbitan boleh dipertimbangkan.

**342/342 draf RPH format teknikal tersedia; 0/342 diluluskan secara akademik. PR staging tidak dipromosikan ke produksi.**
