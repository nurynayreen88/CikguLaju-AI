# Sains Tahun 4 — Audit RPH 79 PdP (7 November 2026)

**Skop:** staging untuk semakan, bukan Telegram/Web pengguna. PR [#442](https://github.com/nurynayreen88/CikguLaju-AI/pull/442).

## Sumber

- DSKP KSSR Semakan 2017 Sains Tahun 4 pemilik (boleh dibaca secara teks): https://drive.google.com/file/d/1eXDdb_qSfCKyqoVtl9T4q2I4rKyHtk9D/view
- Buku Teks asal Tahun 4 pemilik: https://drive.google.com/file/d/1Y2Uf44WX5bFhAaaEx55Is7cZpJfrn7Ms/view — saiz 337,813,479 bait. Pembaca teks pemilik tidak mengeluarkan kandungan. **Jangan anggap halaman sebenar atau aktiviti visual sudah disahkan**.
- Sumber individu PdP `v25.82` yang digunakan dalam draf indeks RPT Sains: **79 PdP** (kod sumber `SCI-Y4-PDP-001` hingga `079`), Unit 2–10. `v26.00` di Render tidak semestinya menggunakan jujukan sama; perlu audit pariti sebelum integrasi.

## Kualiti bahan yang dibangunkan

Bank `web/sains_y4_79_activity_bank_draf_20261107.py` menetapkan 79 pilihan berasingan berdasarkan SP Year4 asal: set induksi, dua aktiviti dengan peranan guru/murid berlainan, hasil PBD spesifik, bahan dan keselamatan. Tiada aktiviti guru cuba menghasilkan RPH dengan AI semasa runtime.

Bank membahagikan tema substantif seperti berikut:

| Unit | PdP | Fokus |
|---|---:|---|
| 2 Manusia | 15 | Sistem pernafasan, perkumuhan/penyahtinjaan, tindak balas |
| 3 Haiwan | 8 | Organ pernafasan, vertebrata/invertebrata |
| 4 Tumbuhan | 9 | Tindak balas rangsangan, fotosintesis |
| 5 Sifat Cahaya | 12 | Cahaya lurus, pantulan, pembiasan |
| 6 Bunyi | 5 | Getaran, perambatan, pantulan, pencemaran |
| 7 Tenaga | 9 | Bentuk tenaga, perubahan, sumber boleh dibaharui |
| 8 Bahan | 7 | Sumber asas bahan dan sifat bahan |
| 9 Bumi | 7 | Graviti, putaran dan peredaran Bumi |
| 10 Mesin | 7 | Tuas, mesin ringkas dan kompleks |
| **Jumlah** | **79** | |

Perubahan dilindungi syarat berikut:

- Tidak menukar `pdp_code`, nombor PdP, Unit, tajuk sumber, SK atau SP dalam DB.
- Aktiviti bercetak mempunyai `Aktiviti 1` dan `Aktiviti 2` serta nombor setiap arahan pada baris baharu.
- Kemahiran Proses Sains Tahun 4 daripada DSKP Tahun 4 dipadankan mengikut aktiviti, bukan menambah SP rasmi atau PdP baharu.
- PBD individu menuntut bukti khusus, bukan semata-mata refleksi generik.
- Tiada nombor halaman Buku Teks direka. Semua 79 fail kekal DRAF/HOLD.
- Kegagalan semakan reka letak Word/PDF ialah kegagalan teknikal; tidak boleh terus melepaskan bahan.

## Ujian staging yang diperlukan

Jalankan dalam CI:

```bash
python -m unittest discover -s tests -p test_sains_y4_79_bank_quality_20261107.py -v
python -m tools.render_sains_rpt_2027_ab_review_20261106
python -m tools.render_sains_y4_79_rph_draf_20261107
python -m tools.check_sains_y4_79_word_a4_20261107
```

Hasil staging selepas lulus: `build/sains_y4_79_rph_DRAF_20261107/`, terdiri daripada 79 Markdown + 79 Word + 79 PDF, bersama CSV manifest dan JSON sebab HOLD. Ujian Word menggunakan LibreOffice; jangan panggil satu halaman sehingga langkah tersebut lulus.

**Belum siap akademik:** 79/79 halaman dan aktiviti buku teks mesti disahkan secara visual; edisi sumber, ketepatan pedagogi dan objektif/PBD perlu semakan guru, kesesuaian keselamatan amali perlu diperiksa, dan fungsi muat turun Telegram/Web sebenar belum diuji. **Peratus subjek 80% tidak boleh diberikan daripada status CI sahaja.**

**Larangan:** tiada import database, reset/overwrite, auto-merge, perubahan pembayaran atau deployment produksi.
