# Sains Tahun 1–6 — audit sumber v26.00 (6 November 2026)

**Keputusan penerbitan: HOLD / BELUM FINAL READY.** Audit ini tidak mengubah DB, RPH, Telegram, Web, kuota, ataupun PDF sedia ada.

## Sempadan fakta

- Susunan master kerja *belum disahkan*: Tahun 1 = 92, Tahun 2 = 92, Tahun 3 = 103, Tahun 4 = 88, Tahun 5 = 116, Tahun 6 = 96; jumlah 587, **bukan** bukti 587 rekod aktif atau 587 RPH lengkap.
- Audit DB terdahulu (September 2026) pernah menemui 385 PdP dalam v25.68. Nombor itu **bukan** status v26.00; semak semula terus daripada binari v26.00.
- Lajur verified_pdp_sequence.pdp_sequence_code, bukan week_no atau bilangan SP, ialah calon identiti PdP; setiap PdP boleh mempunyai beberapa SK/SP.
- RPT dan PDF Sains 2027 masih tiada dalam direktori khusus rpt_2027/sains pada cabang main semasa audit.
- Audit sumber statik tidak mengesahkan kandungan RPH, render A4, atau muat turun Web/Telegram secara langsung.

## Keputusan CI audit sebenar (6 November 2026)

Rujukan: [GitHub Actions run #42177830409](https://github.com/nurynayreen88/CikguLaju-AI/actions/runs/42177830409).

- v26.00: manifest 3 bahagian dan SHA256 sepadan, SQLite quick_check OK.
- Jadual verified_pdp_sequence v26.00 **tiada** lajur pdp_sequence_code dan **0 baris Sains**.
  Tidak boleh menganggap isi RPT atau SK/SP sebagai PdP verified.
- v26.00 masih mempunyai **437 rekod curriculum_standards Sains Tahun 1–6** dan
  **67 entri rpt_entries Sains Tahun 1–6**. Itu ialah rekod standard/entri topik,
  **bukan** 437 atau 67 PdP lengkap.
- Checkpoint v25.68 (rujukan sejarah, bukan sumber runtime yang diluluskan):
  SQLite quick_check OK, saiz 27,848,704 bait, 385 rekod Sains dan 385 kod
  pdp_sequence_code unik. SHA yang *diperhatikan*:
  79845954db3f8a7c9e9b83ac1eb13477b64a92d0b9c12cfcd5ddd799b0f3f53b.
  Tidak ada manifest SHA rujukan bebas untuk checkpoint ini.
- Audit automatik berjaya dijalankan tetapi keputusan akademik **HOLD**.
  Kod menjalankan semakan baca sahaja dan tidak memindahkan 385 rekod itu ke v26.

| Tahun | Sasaran kerja, belum disahkan | Kod PdP unik v25.68 | Rekod sequence Sains v26.00 |
|---|---:|---:|---:|
| 1 | 92 | 43 | 0 |
| 2 | 92 | 51 | 0 |
| 3 | 103 | 45 | 0 |
| 4 | 88 | 79 | 0 |
| 5 | 116 | 83 | 0 |
| 6 | 96 | 84 | 0 |
| **Jumlah** | **587** | **385** | **0** |

**Tindakan teknikal berikutnya:** pastikan enjin Telegram yang aktif membaca
sumber urutan Sains yang mana; jangan hidupkan fallback senyap atau menampal
385 rekod daripada snapshot lama tanpa padanan RPT/DSKP/BT dan semakan integriti.
Setiap pembaikan hendaklah migration bertambah dengan backup dan ujian rollback,
bukan overwrite master. Semak secara individu semua RPH sebelum penerbitan.

## Rujukan bahan dalam Google Drive (lokasi, bukan pengesahan halaman)

| Tahun | DSKP | Buku teks |
|---|---|---|
| 1 | [DSKP](https://drive.google.com/file/d/1-_V_8J_Fr0iQ8xqTP9WbUtv-DNhDaWec/view) | [BT](https://drive.google.com/file/d/1P5uQJHqBXUGM4HOOW6t8AdxB3EWJO4Te/view) |
| 2 | [DSKP](https://drive.google.com/file/d/1rr4CjNvhtI13ioiVSTZi65cvap7j1U6Z/view) | [BT](https://drive.google.com/file/d/1LkJJWUb-zyFJ1ftpHM-4HIpIcEGLORI9/view) |
| 3 | [DSKP](https://drive.google.com/file/d/1n4OM7x2e1_LIaBQDIxyeHmXglImtu5Yb/view) | [BT](https://drive.google.com/file/d/17QNqKZjSF7V9GzzkXkz46bDJGnyKYq-F/view) |
| 4 | [DSKP](https://drive.google.com/file/d/1eXDdb_qSfCKyqoVtl9T4q2I4rKyHtk9D/view) | [BT](https://drive.google.com/file/d/1Y2Uf44WX5bFhAaaEx55Is7cZpJfrn7Ms/view) |
| 5 | [DSKP](https://drive.google.com/file/d/1YkiK-pVo4UUzyOUvv_Vrico58eQyddCz/view) | [BT](https://drive.google.com/file/d/1m5k8gVkNImT8QEdw6fCEVpQh_tNkUKUT/view) |
| 6 | **Belum ditemui dalam folder sumber semasa** | [BT](https://drive.google.com/file/d/14yto0qTq87FIeo6UtJuDef8D2xGwiPLd/view) |

Sumber PDF belum diaudit halaman demi halaman; pautan di sini tidak mengesahkan SK/SP atau nombor halaman. Tahun 1 memerlukan semakan berasingan terhadap pelaksanaan KP2027 sebelum penerbitan guru.

## Turutan pelepasan yang selamat

1. Audit binari v26.00 berasaskan manifest SHA: jumlah sebenar unik per tahun, kod PdP, SP berbilang, pengecualian, kecacatan unit, serta ketiadaan BT.
2. Padankan *setiap PdP yang benar-benar wujud* dengan DSKP, RPT 2026 yang disahkan, buku teks dan kemahiran proses sains; rekod sumber/bukti halaman.
3. Bina RPT 2027 Kumpulan A/B landscape dengan muka depan mengikut contoh English, nombor PdP sebenar, takwim dan cuti negeri — tanpa mengubah identiti PdP menjadi minggu.
4. Uji setiap RPH Word/PDF (struktur A4, aktiviti Sains khusus, SK/SP lengkap, tarikh DD/MM/YYYY, kelas, masa) dan muat turun sebenar Telegram/Web.
5. Hanya selepas QA individu dan rollback tersedia, kelulusan penerbitan diberikan. Tiada auto-merge, auto-migration atau auto-deploy.

## Arahan audit

- python -m unittest discover -s tests -p test_sains_v26_source_inventory_20261106.py -v
- python tools/audit_sains_v26_readonly_20261106.py

Output JSON ialah *inventori teknikal*, bukan kelulusan RPH.
