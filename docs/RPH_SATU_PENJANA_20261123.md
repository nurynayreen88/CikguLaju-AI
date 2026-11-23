# Pelan satu penjana RPH CikguLaju — 23 November 2026

## Keputusan pemilik

Semua subjek dan Tahun 1–6 akan berkongsi **satu enjin RPH** untuk tetapan bentuk Word/PDF. Sumber pembelajaran kekal berasingan mengikut SK, SP, Lesson/PdP, jenis sekolah dan bahasa; **jangan satukan fail pangkalan data** atau menukar aktiviti semata-mata untuk memudahkan reka bentuk.

**Master visual:** BM SK KP2027 Tahun 1; rujuk `docs/RPH_MASTER_BM_SK_KP2027_T1_20261123.md`.

## Bentuk akhir

- `Sumber Kurikulum` (SK, SJKC, SJKT, KP2027, DLP, PPKI, PI, BA dan lain-lain): hanya mengambil data yang sudah wujud dan telah disahkan, tanpa mereka medan yang tiada.
- `Penyesuai / adapter`: menukar struktur data kepada payload RPH sejagat: identiti/tajuk, metadata guru yang wujud, baris standard/objektif sedia ada, aktiviti asal, pentaksiran dan refleksi asal. **Tiada tambahan kandungan akademik.**
- `Penjana RPH sejagat` (`web/rph_unified_engine.py`): satu pintu masuk terkawal untuk menghasilkan Word atau PDF. Token reka bentuk berkongsi warna neutral panel guru dan arah LTR/RTL. Subjek LTR = guru kanan; PI/BA RTL = guru kiri.
- `Penyampaian`: Web/Telegram memanggil penjana dengan sumber pilihan serta semakan akses/kuota masing-masing. Menyatukan reka bentuk **tidak membenarkan memintas** auth, langganan, bayaran atau kawalan akses.
- **Peraturan keselamatan:** penyesuai yang belum diaudit mesti kekal menggunakan penjana sedia ada; jangan tukar tanpa pemeriksaan Word/PDF sebenar.

## Kemajuan migrasi (status tepat)

| Keluarga | Sumber | Pintu masuk sejagat | Catatan |
|---|---|---|---|
| DLP Science & Mathematics | `dlp_year2_rph.py` | **Disambung dan diuji** | `render()` menghantar payload sedia ada ke `render_structured_rph`; dalaman `_word/_pdf` dikekalkan untuk keserasian, bukan ditulis semula |
| PPKI Pengurusan Kehidupan pilot | `staging/ppki/render_pengurusan_kehidupan.py` | **Disambung dan diuji** | Memanggil pintu masuk yang sama dengan DLP; HTML/PDF/Word dan data sumber asal tetap dilindungi |
| KSSR native LTR sembilan subjek | `web/rph_premium_header_20261121.py`, `web/rph_native_pdf_header_20261121.py` | **Tetapan panel guru dipusatkan; penjana lama belum dipindah** | Warna guru kini dibaca dari satu token sejagat; menukar generator melibatkan QA teks SK/SP, Word dan PDF sebenar |
| Sains SK Tahun 2–6 | beberapa penjana / laluan | **Belum dipindah** | Ada bahan audit/draf; perlu petakan laluan siap satu persatu |
| KP2027 Tahun 1 | sumber & penjana khusus | **Belum dipindah** | Rujukan reka bentuk ini tidak boleh dimusnahkan semasa migrasi |
| English integrated / standalone / SJKC/SJKT | laluan sendiri | **Belum dipindah** | Kekalkan Lesson, sumber buku, audio dan rujukan sedia ada |
| Pendidikan Islam/Jawi dan Bahasa Arab | RTL, fon serta sumber khas | **Belum dipindah** | Perlu adapter RTL sebenar, bukan pembina LTR dengan teks sekadar dialih |
| PPKI lain, DLP lain jika penjana berasingan | belum dipetakan sepenuhnya | **Belum dipindah** | Tidak boleh dianggap termasuk hanya kerana contoh Tahun 2 lulus |

## Syarat sebelum migrasi seterusnya

1. Ambil **satu Word dan satu PDF sebenar** daripada penjana subjek/tahun berkenaan.
2. Bandingkan SK/SP, tajuk, halaman, objektif, langkah PdP, BBM, pentaksiran, refleksi dan metadata guru sebelum/selepas. Teks hendaklah kekal.
3. Bentuk A4 profesional sama: tepi kotak luar sejajar, identiti pastel, panel guru neutral, kotak guru kanan LTR/kiri RTL. Hanya cetak baris asal; tiada tajuk Auto/Manual pada refleksi.
4. Semak bahawa fail PDF tidak mempunyai kotak bertindih; Word tidak melebihi margin; Jawi/Arab tidak rosak; muat turun Web tidak membuka tab yang tidak diperlukan.
5. Ujian regresi CI dan penerbitan Render lulus **sebelum** ditandakan aktif. Ujian tidak menggunakan kuota guru.

## Mengapa bukan gabung semua sumber ke satu fail besar?

Satu fail besar yang mencampurkan penghasilan RPH dengan sumber 16+ subjek menyukarkan pembetulan dan berisiko mengubah SK/SP. **Satu API serta satu pustaka reka bentuk** memberikan satu tempat untuk ubah suai, sementara adapter mengekalkan integriti kurikulum. Inilah maksud `satu penjana` yang akan dipakai.
