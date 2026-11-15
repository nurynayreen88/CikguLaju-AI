# Audit baharu buku teks RBT Tahun 4 — semakan langsung pada PDF asal
**Tarikh:** 7 November 2026
**Status:** SEMAKAN KOD-HALAMAN TEKS LULUS, **BUKAN** pengesahan latihan/visual, aktiviti, keselamatan atau kelulusan guru.

## Kaedah pengesahan

Sumber: [Buku Teks RBT Tahun 4 SK, PDF asal dalam Drive](https://drive.google.com/file/d/1wh6Ilh0yo8jUHNh0Wk5OLvzUngXkxLYH/view), **104 halaman PDF** (124 MB). Pemeriksaan menggunakan PyMuPDF `Page.get_text()` secara langsung atas fail PDF asal, tanpa OCR.

Audit sumber terdahulu: `audits/rbt_t4_textbook_sp_page_map_20261106.json`, mengandungi 57 kod SP dan senarai halaman bercetak. Offset: halaman bercetak **n** muncul pada PDF halaman **n+6** (1-based). Setiap rujukan halaman diuji supaya teks PDF pada halaman tersebut benar-benar mengandungi **kod SP yang sama**, bukan hanya berdasarkan urutan unit.

| Pemeriksaan | Hasil |
|---|---:|
| Dokumen PDF asal | 104 halaman |
| Kod SP dalam ledger yang diperiksa | 57/57 |
| Padanan kod SP pada halaman bercetak yang ditetapkan | **61/61** |
| Kod SP dengan sekurang-kurangnya satu halaman gagal | **0** |
| Status kelulusan visual/aktiviti setiap PdP | **0/32** |
| Dokumen asal / CSV / RPH / PDF live ditimpa | **Tidak** |

Checksum SHA-256 fail PDF sumber untuk reproducibility:
`8964ad3f0789ae825041294b5327ddc6bd6a40af3f8e5c835543157ffc1f9780`

### Sampel pemeriksaan visual langsung (bukan kelulusan menyeluruh)

Sampel halaman bercetak 4, 7, 9, 11, 34, 45, 68, 86, 97 telah dibuka sebagai imej daripada PDF:
- m/s 4/7: peraturan dan simbol keselamatan bengkel;
- m/s 9/11: contoh langkah apabila kemalangan dan amalan penyelenggaraan peralatan;
- m/s 34/45: pembinaan produk/lakaran reka bentuk;
- m/s 68/86/97: reka bentuk makanan, fitur antara muka Scratch, pembentangan hasil atur cara.

Sampel ini mengesahkan **kewujudan konteks pembelajaran pada halaman**; ia tidak bermaksud arahan latihan, kesesuaian prosedur kerja, keselamatan alat atau aktiviti guru telah disahkan bagi 32 PdP.

## Hasil tindakan

Kod SP dan halaman tercetak Tahun 4 kini mempunyai bukti pemeriksaan tekstual terus dari PDF asal, melampaui bukti ledger yang hanya menyatakan halaman calon. Penanda dalam RPH/RPT kekal `DRAF` kerana penyemakan visual individu setiap PdP dan kelulusan pedagogi belum dilaksanakan. Jangan tukar status `release_ready` atau `halaman_buku_disahkan` kepada `true`.

**Penjana audit boleh diulang pada sumber asal:**
```bash
python scripts/verify_rbt_t4_textbook_pages_offline.py \
  --pdf /path/to/GuruBesar_BukuTeks_RBT_T4_SK.pdf \
  --out /tmp/rbt_t4_page_proof.json
```

**Tahun 5–6:** sumber halaman dalam `audits/rbt_y5_y6_textbook_page_evidence_20261106.json` berpunca daripada salinan digital awam, belum diberi bukti tahap PDF asal yang setara. Tidak dibenarkan menganggap padanan 61/61 Tahun 4 meliputi T5–6.

## Release gate

Kesemua 96 RBT dalam PR #441 kekal **STAGING / DRAF**. Agihan minggu simulasi M03–M34 kekal berasingan dan bukan jadual sebenar. Sambungan ke Web/Telegram tidak dibuat.
