# RPT 2027 — Manifest baris Tahun 2 (27 Oktober 2026)

Audit sebenar dijalankan pada salinan DOCX asal tanpa mengubah fail sumber.

| Metrik | Pendidikan Islam Tahun 2 | Pendidikan Jasmani Tahun 2 |
|---|---:|---:|
| Jadual | 38 | 17 |
| Baris | 166 | 62 |
| Baris dengan token tarikh | 126 | 45 |
| Baris tanpa token tarikh | 40 | 17 |

**Jumlah:** 228 baris, 171 memerlukan semakan tarikh, 57 baris tanpa token tarikh.

SHA-256 sumber:
- PI: `e5328102b4d059616ede2adf5cdf3a357acf1c0d997a2472e135fa120fcb7845`
- PJ: `139943622b893f218d90e63816104650afbeebae8e90f02dac0b44baa7e24242`

Kaedah: python-docx, baca setiap jadual/baris/sel, ID stabil `PI_T2-Txx-Rxxx` / `PJ_T2-Txx-Rxxx`, SHA-256 teks setiap baris; regex token tarikh. Ujian `python -m py_compile` lulus pada skrip pemprosesan tempatan.

**Had:** Baris jadual bukan PdP unik. Baris bertarikh belum disahkan sebagai tarikh sekolah 2027. Kandungan SK/SP dan Jawi belum dinilai untuk kelulusan pedagogi. Tiada penukaran tarikh dibuat. Dokumen Word 2027 belum READY. Tiada DB, fail Drive asal atau produksi diubah.

Sumber Drive:
- PI https://docs.google.com/document/d/1A4Xpdv_slwC86L9N90pMSjZut_tDABYP/edit
- PJ https://docs.google.com/document/d/1iYXEatUbSTbV1B4QqLDJsRx_YrW_KsFF/edit
