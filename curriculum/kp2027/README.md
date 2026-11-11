# CikguLaju — KP2027 Tahun 1 dan Tingkatan 1

**DRAF AUDIT SUMBER · 6 NOVEMBER 2026 · BUKAN RPH/RPT SEDIA GUNA.**

Modul ini ialah permulaan berasingan untuk Kurikulum Persekolahan 2027 (KP2027). Pelaksanaan berfasa bermula dengan **Tahun 1 dan Tingkatan 1 pada 2027**. CikguLaju perlu mengekalkan kurikulum lama untuk kohort lain dan tidak menggunakan RPH KSSR/KSSM sebagai pengganti KP2027.

## Hasil dalam cabang ini

- `source_inventory_20261106.json`: 21 calon rekod subjek — Tahun 1 (8) dan Tingkatan 1 (13). Rekod menyatakan pautan asal serta tahap pembuktian, **bukan** pemetaan standard yang telah diluluskan.
- `inventory.py`: enjin carian subjek dan status KP2027 yang **fail-closed**. `request_rph` / `request_rpt` tidak akan memulangkan RPH lama atau menjana standard palsu.
- `staging_schema.sql`: skema SQLite sidecar **berasingan** untuk menyimpan DK yang diperoleh kemudian: URL sumber, versi, SHA-256 PDF, halaman asal, jenis/kod/teks standard sebenar, pengesahan manusia, dan pemetaan kepada nombor PdP. Skema belum dijalankan terhadap DB produk.
- `web/kp2027_status_api.py`: API status dalaman ber-token, hanya untuk staging selepas diaktifkan secara eksplisit. RPH/RPT baharu belum dibuka.
- Ujian `tests/test_kp2027_y1_f1_source_gate_20261106.py` membuktikan pemisahan Tahun 1 dan Tingkatan 1, penahanan SK/SP, keutuhan skema dan akses terhad.

### Sumber yang dijejak

| Peringkat | Kandungan | Bukti yang ditemui | Pengesahan kandungan DK |
|---|---|---|---|
| Tahun 1 | Bahasa Melayu SK | [Penataran PPD Johor Bahru](https://sites.google.com/moe-dl.edu.my/kpbmthn1jb2027/home) | Menunggu PDF asal |
| Tahun 1 | Matematik | [Penataran Matematik sekolah](https://sites.google.com/moe-dl.edu.my/panitia-matematik-skk/kualiti-guru/ldp/ldp-2026) | Menunggu PDF asal |
| Tahun 1 | Alam dan Manusia | [Portal DK dan penataran](https://sites.google.com/moe-dl.edu.my/gurupenataranalamdanmanusiakp2/home) | Dokumen disenaraikan; fail tidak diakses |
| Tahun 1 | Pendidikan Islam, Bahasa Arab | [PPD Saratok](https://sites.google.com/moe-dl.edu.my/upippdsaratok/kp-2027) | DK disenaraikan; capaian fail disekat |
| Tingkatan 1 | Matematik | [Portal DK Matematik T1](https://sites.google.com/moe.gov.my/kp2027-matematik-tingkatan-1/bahan-rujukan) | Dokumen disenaraikan; belum diekstrak |
| Tingkatan 1 | Pendidikan Islam, Bahasa Arab | [PPD Saratok](https://sites.google.com/moe-dl.edu.my/upippdsaratok/kp-2027) | DK disenaraikan; belum diaudit |
| Tingkatan 1 | Sejarah | [Kenyataan rasmi KPM 11 Feb 2026](https://www.moe.gov.my/storage/files/shares/Kenyataan%20Media/KM2026/KM%20KPM%20Berhubung%20Kurikulum%20Baharu%20Mata%20Pelajaran%20Sejarah%20Sekolah%20Rendah%20Hanya%20Ditawarkan%20Kepada%20Murid%20Tahun%205%20Dan%20Tahun%206.pdf) | Penawaran subjek disahkan; DK belum diperoleh |

Subjek lain dalam inventori mempunyai bukti penataran/laporan sahaja, bukan naskhah DK yang telah disahkan. Jumlah 21 ialah **skop penjejakan pertama**, bukan pengesahan struktur rasmi seluruh sekolah.

### Peraturan penting

1. Tahun 1 gunakan **Alam dan Manusia** sebagai indeks KP2027; jangan tampal RPH Sains KSSR Tahun 1 sebagai pengganti.
2. **Sejarah bukan subjek Tahun 1 KP2027** menurut kenyataan KPM; Sejarah Tingkatan 1 termasuk skop.
3. Program Pembentukan Karakter direkod sebagai `programme`, bukan diada-adakan sebagai standard subjek atau Unit/PdP.
4. Apabila PDF DK sebenar berjaya dimuat turun: sahkan penerbit, edisi, tarikh, hash fail dan halaman; kemudian semak SP/SPi/TP **berdasarkan istilah sebenar dokumen**, bukan kod daripada DSKP lama.
5. Satu rekod standard hanya boleh diluluskan selepas semakan manusia terhadap halaman PDF. Kandungan RPH mesti mempunyai objektif, tiga langkah aktiviti terperinci guru-murid, BBM dan evidens pentaksiran yang sepadan dengan standard disahkan.
6. RPT Kumpulan A/B hanya dibina selepas liputan standard, bilangan PdP, peruntukan waktu dan kalendar sekolah dipastikan. Nombor PdP tidak sama dengan minggu takwim.
7. **Jangan** gabungkan sumber KP2027 dengan SQLite produksi KSSR/KSSM. Tiada reset, overwrite atau silent fallback.

### API dan ujian

Register hanya di persekitaran staging pada aplikasi Telegram (bukan Web terbuka):

```python
from web.kp2027_status_api import register_if_enabled
register_if_enabled(app)
```

Prasyarat: `CIKGULAJU_KP2027_STAGING_ENABLED=1` dan `CIKGULAJU_AUTHORITATIVE_API_TOKEN` sekurang-kurangnya 32 aksara. Token hanya untuk panggilan backend-to-backend, tidak boleh dimasukkan dalam halaman Web.

- GET `/internal/kp2027/v1/levels`: Tahun 1 dan Tingkatan 1.
- GET `/internal/kp2027/v1/subjects?level=Tahun%201`: senarai calon dan tahap pengesahan.
- GET `/internal/kp2027/v1/status?level=Tingkatan%201&subject=Matematik&source_digest=<SHA256>`: status sumber tertentu.
- GET `/internal/kp2027/v1/standards?level=...&subject=...`: HTTP 503 sehingga DK dan SP disahkan.
- POST `/internal/kp2027/v1/render`: HTTP 503 selagi RPH/RPT KP2027 belum diluluskan.

Jalankan: `python -m unittest discover -s tests -p 'test_kp2027_y1_f1_source_gate_20261106.py' -v`.

### Syarat naik taraf daripada DRAF kepada READY

- [x] Sumber portal dan calon dokumen ditemui untuk kedua-dua peringkat.
- [x] Asas katalog berasingan dan perlindungan SK/SP palsu disediakan.
- [ ] Naskhah PDF DK KP2027 diperoleh/difailkan bersama hash dan versi.
- [ ] Semua SP/SPi yang berkaitan dibaca dan disahkan mengikut halaman.
- [ ] Pemetaan lengkap tema/unit/topik → PdP dan RPT Kumpulan A/B disahkan.
- [ ] RPH Word/PDF satu A4 bagi setiap PdP disemak individu.
- [ ] UI Telegram/Web menggunakan satu sumber, dengan kawalan akses, kuota dan ujian muat turun.
- [ ] Ujian bukan-regresi sistem lama, kelulusan pengguna dan penerbitan bertahap.

**Status sebenar: belum ada standard Tahun 1 atau Tingkatan 1 yang disahkan sebagai READY dalam modul ini.** Bahan berfungsi sebagai inventori dan laluan sumber, bukan janaan RPH KP2027.

## Batch editorial 7 November 2026 (draf sahaja)

- **24 contoh RPH asli** bagi 8 kombinasi peringkat–subjek (Tahun 1: Alam dan Manusia, Bahasa Melayu, Matematik, Pendidikan Islam, Bahasa Arab; Tingkatan 1: Matematik, Pendidikan Islam, Bahasa Arab), tiga contoh setiap satu.
- Semak kandungan dalam [candidate_rph_batch_20261107.md](candidate_rph_batch_20261107.md). Data struktur semakan berada dalam [candidate_rph_batch_20261107.json](candidate_rph_batch_20261107.json).
- Kesemua contoh mempunyai aktiviti guru/murid, BBM, PBD, pembezaan dan nilai karakter tetapi **tiada kod SK/SP/SPi rasmi**, belum ada jadual RPT, belum diaudit terhadap DK asal, dan **tidak diluluskan untuk Telegram/Web/DB produksi**.
- Ujian metadata baharu: `python -m unittest discover -s tests -p 'test_kp2027_candidate_rph_20261107.py' -v`.
- Semua label `C01`–`C03` ialah **nombor calon editorial**, bukan nombor PdP kurikulum sebenar. Fail ini tidak ditafsir sebagai bahan READY. Muat turun PDF/Word hanya boleh dijana selepas audit sumber dan kelulusan setiap PdP.
