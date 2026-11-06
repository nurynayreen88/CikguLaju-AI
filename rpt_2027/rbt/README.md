# RBT CikguLaju 2027 · Tahun 4–6 · DRAF TERKAWAL

**KEPUTUSAN SEMAKAN: STAGING / REVIEW-READY, BELUM FINAL READY UNTUK PENGGUNA.**

Sumber RBT dan penghala Telegram/Web telah dibangunkan. Kod Telegram dan Web sudah berada dalam cabang perkhidmatan masing-masing, tetapi pengaktifan pengguna memerlukan flag eksplisit `CIKGULAJU_RBT_2027_DRAFT_USER_ENABLED=1`, yang secara lalai tidak diaktifkan. Ini bukan pengesahan muat turun pengguna sebenar. Jangan aktifkan sebelum semua perakuan diterima.

## Inventori dan liputan DSKP

| Tahun | Unit sebenar dalam buku teks | Agihan 32 PdP cadangan | Kod SP DSKP |
|---|---|---|---|
| 4 | 6: Keselamatan Bengkel, Pengenalan kepada Reka Bentuk, Pengenalan kepada Teknologi, Pembungkusan, Makanan, Pengaturcaraan | 3 + 7 + 4 + 5 + 5 + 8 | 57 |
| 5 | 4: Teknologi Rumah Tangga, Aplikasi Reka Bentuk Teknologi Kejuruteraan, Reka Bentuk Pengaturcaraan, Teknologi Pertanian | 6 + 6 + 12 + 8 | 34 |
| 6 | 3: Aplikasi Reka Bentuk Teknologi Kejuruteraan, Reka Bentuk Pengaturcaraan (Robotik), Pembangunan Produk | 10 + 10 + 12 | 23 |

Jumlah **96 RPH (32 setiap tahun)**, **3 RPT 2027**, **114 kod SP**. Peruntukan 32 jam setahun ialah panduan DSKP, bukan tarikh atau Lesson rasmi KPM. Keputusan berkenaan urutan Unit/PdP yang disediakan CikguLaju adalah cadangan perancangan.

Setiap RPH: set induksi 5 minit, aktiviti utama 15+25 minit, pengukuhan/PBD 10 minit, penutup 5 minit; SK/SP, objektif, bahan, keselamatan dan evidens kerja.

## Bukti kualiti dan QA (6 November 2026)

- **114/114 SP** telah dipadankan dengan ayat fokus sebenar dalam tiga PDF DSKP asal melalui semakan teks tepat: `audits/rbt_2027_114_dskp_exact_text_evidence_20261106.json`.
- **96/96** RPH dan RPT mempunyai ID PdP, tajuk, Unit dan SK/SP sepadan; semakan: `scripts/check_rbt_2027_pedagogy_qa.py`.
- **60 PdP** menerima suntingan manual khusus semantik dalam pusingan ini (Y4=32, Y5=16, Y6=12). Antaranya: situasi tindakan keselamatan, lakaran (bukan pseudokod), pembentangan sebenar, pemilihan medium tanaman, carta alir robot, kod, penyambungan dan ujian fungsi. Semakan regresi: `scripts/check_rbt_2027_source_semantics.py`.
- **20 PdP** yang mengulang SP merentas sesi dibezakan mengikut tahap kerja, bukan aktiviti disalin.
- CI `.github/workflows/rbt-2027-staging-qa.yml` menjana 96 RPH Word + 96 PDF **satu halaman A4 potret**, bersama 3 RPT Word + 3 PDF **A4 landscape** dengan muka depan. Kesemua 99 Word / 99 PDF disemak automatik. **Ini ujian fail contoh oleh CI, bukan kelulusan penjana natif pengguna.**
- Menu Telegram Tahun→Subjek RBT→Unit→PdP dan API Web dengan penjana Word/PDF serta token pengesahan diuji dalam persekitaran simulasi. Quota/10 janaan, Rakan Pembangun dan langganan asal tidak diubah.
- Rujukan buku teks Tahun 4: PDF 104 halaman daripada Drive; 57/57 kod SP ditandai mengikut halaman bercetak; sampel visual merentas enam unit telah dilihat. **Tidak sama dengan pengesahan aktiviti satu per satu.**
- Buku Tahun 5: sumber awam `https://anyflip.com/bonxz/ipnx/basic`; calon halaman SP 7.1.6 dibetulkan daripada **77–80** kepada **77–81** selepas semakan teks.
- Buku Tahun 6: `https://fliphtml5.com/rjdzf/cwso/basic`; pastikan edisi SK **2021** ISBN **978-983-49-3283-1**, bukan edisi 2015. Padanan halaman masih **calon**, belum kelulusan visual individu.

## Kekangan penerbitan

1. Kelulusan pedagogi/guru individu masih **0/96** (manifest: `audits/rbt_t4_t6_manual_release_approval_manifest_20261106.json`).
2. Kelulusan gambar/aktiviti buku teks individu masih **0/96**. Kehadiran kod SP dan teks buku sahaja tidak membuktikan semua arahan, gambar dan latihan sesuai.
3. Ujian pengguna sebenar (Telegram dan Web, termasuk akaun percubaan/berbayar, Word/PDF, kelas dan jadual) belum diluluskan. Pengujian API simulasi tidak sama dengan ujian Render LIVE.
4. Tarikh RPT 2027 Kumpulan A/B serta cuti umum/cuti negeri/cuti gantian perlu diselaraskan dengan takwim sekolah dan jadual waktu guru. Fail tidak mereka-reka tarikh.
5. Flag penerbitan kekal **OFF** dan semua rekod `review.release_ready=false`. Jangan menukarkan status semata-mata kerana ujian teknikal lulus.

Semakan keseluruhan:

```bash
python scripts/check_rbt_t4_t6_2027.py
python scripts/check_rbt_2027_pedagogy_qa.py
python scripts/check_rbt_2027_source_semantics.py
python scripts/check_rbt_2027_source_adapter.py
```

Laluan kerja: PR #427 untuk kandungan/pemurnian; PR #410 (Telegram) dan #411 (Web) telah digabungkan lebih awal. Sumber tetap sama; perubahan tidak menyentuh pangkalan data atau hak akses pengguna.
