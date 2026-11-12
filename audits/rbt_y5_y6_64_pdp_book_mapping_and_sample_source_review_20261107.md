# RBT Tahun 5–6 — audit silang 64 PdP RPH/RPT/ledger dan semakan buku teks sampel

**Tarikh:** 7 November 2026  
**Status:** STAGING DRAF — konsistensi data lengkap, pengesahan visual/aktiviti dan kelulusan guru belum selesai.

## Audit 64/64 PdP (bukti dalaman)

Audit automatik `scripts/audit_rbt_y5_y6_64_pdp_page_consistency_staging.py` membaca sumber berasingan:
1. ledger `audits/rbt_y5_y6_textbook_page_evidence_20261106.json`;
2. `RPH_RBT_T5_2027_DRAF.json` dan `RPH_RBT_T6_2027_DRAF.json`, 32 PdP/tahun;
3. `RPT_RBT_T5_2027_DRAF.csv` dan `RPT_RBT_T6_2027_DRAF.csv`;
4. `audits/rbt_t4_t6_manual_release_approval_manifest_20261106.json`.

| Jenis audit dalaman | T5 | T6 |
|---|---:|---:|
| PdP RPH/RPT/manifest mempunyai identiti, urutan, kod SK/SP sama | 32/32 | 32/32 |
| Setiap kod SP mempunyai calon julat halaman yang sama dalam RPH/ledger | 32/32 | 32/32 |
| Teks `Rujukan Buku Teks m/s` CSV sepadan julat calon dengan status semakan | 32/32 | 32/32 |
| Senarai halaman calon pada manifest semakan manual sepadan ledger | 32/32 | 32/32 |
| Rekod kelulusan guru/halaman/aktiviti/tarikh calon tersalah naik sebagai READY | 0 | 0 |
| Rujukan SP unik dalam ledger | 34 | 23 |

**Jumlah: 64/64 PdP dalaman konsisten.** Ini bukan bukti 64/64 halaman buku benar-benar diperiksa secara visual.

Output GitHub Actions tersimpan berasingan sebagai `staging/rpt_2027_seragam_2026/audit_rbt_y5_y6_64_pdp_page_consistency.json` dalam artifak CI. Semakan ini *fail closed* jika kod, julat, identiti, unit, kelulusan atau turutan berubah. `independent_book_page_checks_completed` = 0 **untuk audit komprehensif automatik**; jangan tandakan `halaman_buku_disahkan` atau `release_ready`.

## Bukti sumber buku teks awam — sampel sahaja

### Tahun 5

Sumber [Buku Teks RBT Tahun 5 SK, AnyFlip](https://anyflip.com/bonxz/ipnx/basic) memaparkan label halaman bercetak dan kod:
- SP **4.3.1**, m/s **4–6**: konteks jenis mata jahitan (juga mengandungi nota guru);
- SP **4.3.2**, m/s **7–9**: peralatan dan fungsi jahitan serta amalan keselamatan;
- SP **6.4.6**, m/s **60**: pindahkan atur cara pada perkakasan dan uji fungsi;
- SP **7.1.6**, m/s **77–80**: proses sistem penanaman takungan, keselamatan semasa memotong dan menggunakan cat.

URL bahagian kedua: https://anyflip.com/bonxz/ipnx/basic/51-90 .

Ini **sampel label kod dan fokus**, bukan bukti keseluruhan 34 SP atau kesahihan semua langkah aktiviti.

### Tahun 6

Sumber [Buku Teks RBT Tahun 6 SK, FlipHTML5](https://fliphtml5.com/rjdzf/cwso/basic) mengenal pasti **cetakan pertama 2021** dan ISBN **978-983-49-3283-1**. Bahagian halaman yang boleh dibaca menampakkan:
- SP **5.2.1**, m/s **2**, topik komponen elektromekanikal;
- SP **5.2.5**, m/s **11–20**, konteks model kereta/alat kawalan jauh, penyambungan komponen dan keselamatan guru.

Bahagian [m/s 51–76](https://fliphtml5.com/rjdzf/cwso/basic/51-76) disenaraikan tetapi teks halaman penuh tidak dapat diperiksa dengan andal melalui paparan bacaan semasa. Oleh itu **SP 8.1.1–8.1.7 belum mendapat semakan sumber visual penuh dalam audit ini**. Jangan menyatakan kesemua 23 SP Tahun 6 telah diluluskan daripada sampel ini.

## Perbezaan kaedah dan kesimpulan

Semakan ini **melengkapkan**, bukan menggantikan, keputusan Tahun 4 yang mempunyai PDF asal 104 halaman dan 61/61 padanan kod–halaman. Bagi Tahun 5–6, pengesahan visual penuh dan rujukan latihan untuk 64 PdP masih tertangguh. Buku teks digunakan sebagai rujukan isi, bukannya penetapan automatik aktiviti projek yang mesti sama dengan contoh.

**CI:** https://github.com/nurynayreen88/CikguLaju-AI/actions/runs/42317847385 — PASS, 24 PDF staging (21 asas + 3 simulasi), audit JSON baharu.  
**Artifak:** https://github.com/nurynayreen88/CikguLaju-AI/actions/runs/42317847385/artifacts/13550699081

## Pagar release

- 96 PdP RBT Tahun 4–6 masih DRAF kerana kelulusan guru dan semakan latihan/buku belum lengkap.
- Minggu simulasi M03–M34 **bukan** tarikh kelas sebenar; CSV sumber masih tiada jadual A/B.
- 12 tajuk RBT yang terpotong diperbaiki dalam PDF staging sahaja; sumber RPH/CSV asal dikekalkan.
- Muka depan RPT hanya memerlukan logo, nama sekolah, nama guru; pengambilan automatik profil belum disambung.
- PR #441 jangan merge/deploy sehingga audit kandungan dan pihak sekolah meluluskan.
