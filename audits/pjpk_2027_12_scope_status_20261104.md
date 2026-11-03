# PJPK CikguLaju 2027 — matriks 12 skop dan gerbang keluaran
**Audit terakhir:** 4 November 2026
**Status umum:** DRAF / STAGING, **BUKAN READY**. Tiada penggabungan ke `main`, pengubahsuaian DB atau deployment.

## Inventori 237 fail RPH yang disimpan dalam PR #169

| Tahun | Komponen | Fail RPH draf | Status / sumber | Punca belum READY |
|---|---|---:|---|---|
| 1 | PJ | 0 | DK khusus KP2027 Tahun 1 belum disahkan | Tidak boleh guna kod KSSR 2015 sebagai KP2027. |
| 1 | PK | 0 | KP2027 menempatkan unsur Kesihatan dalam Alam dan Manusia Tahap I | Perlu dokumen kurikulum Alam dan Manusia Tahun 1 yang disahkan; **jangan jana subjek PK berasingan daripada DSKP lama**. |
| 2 | PJ | **41** = 37 asal + 4 sisipan akuatik | [RPT staging 37+4](https://docs.google.com/document/d/1nOnaS3O9IBk-ZNcDGRUBtU8k2FCUnOGh1m8WU0ZgSDs/edit), DSKP T2 | Pengesahan isi/Word A4, keselamatan kolam, jadual/takwim; empat sisipan tidak diluluskan. |
| 2 | PK | **18** | [PR #15 — editorial sumber 7+11](https://github.com/nurynayreen88/CikguLaju-AI/pull/15), DSKP T2 | ID sumber belum terikat kepada PdP 2027; rekod pasangan (2232,2352) dan (2252,2353) mungkin bertindih. |
| 3 | PJ | **38** | [RPT Tahun 3 v4](https://docs.google.com/document/d/1OrRrdI-TzpRjsXuukmo4JwafkJil-cE6/edit) | Semakan teks dan pelaksanaan, 1 halaman A4, bot. |
| 3 | PK | **9 draf tematik SK** | [RPT PK Tahun 3 2026](https://docs.google.com/document/d/1L1Jw_XaaZuZF19PSWFxr7b78rejDg3EB/edit) dan DSKP T3 | Sembilan SK (1.1 hingga 9.1) ada RPH calon tanpa ID PdP; baris RPT 2026 bertindan berdasarkan tahap penguasaan. Belum ada nombor PdP 2027 sah. |
| 4 | PJ | **34** | [Indeks v54](https://docs.google.com/document/d/1DjQSztYXVGUes94T0xt3EEMCkAeDNrGXq6-SBzfvsdU/edit) dan DSKP T4 | Sebahagian halaman buku teks belum sah; semak kesesuaian aktiviti, A4, bot. |
| 4 | PK | **9 draf tematik SK** | DSKP PJPK Tahun 4 (akil baligh, keselamatan diri, pemakanan, dll.) | RPH tematik sahaja; belum dipadankan dengan nombor PdP 2027, buku teks, Word A4 dan bot. |
| 5 | PJ | **33** | Indeks v54 dan DSKP T5 | Sesi dengan SP berulang perlukan objektif berbeza; halaman, A4, bot. |
| 5 | PK | **12** = 3 sumber + 9 tematik SK | [PR #15 — editorial PK Tahun 5](https://github.com/nurynayreen88/CikguLaju-AI/pull/15), DSKP T5 | Tiga ID sumber berasingan daripada sembilan calon tematik; pertindihan perlu dipadankan sebelum nombor PdP 2027, A4 dan runtime. |
| 6 | PJ | **34** | Indeks v54 dan DSKP T6 | **PdP 033**: SP 5.2.2 tidak mempunyai SK 5.2 pada entri RPT dan teks 5.2.2 RPT 2026 bercanggah dengan DSKP T6; **konflik sumber**, semak sebelum penerbitan, A4, bot. |
| 6 | PK | **9 draf tematik SK** | DSKP PJPK Tahun 6, SK 1.1 hingga 9.1 | Calon tematik masih perlukan pemetaan RPT PdP 2027, buku teks, Word A4 dan runtime. |

**Jumlah:** 180 PJ + 57 PK = **237 fail** draf; termasuk 4 sisipan akuatik dan 36 calon tematik PK Tahun 3–6 tanpa ID PdP 2027. **Bukan** jumlah RPH diluluskan atau aktif dalam produksi. Manifest fail disimpan di `audits/pjpk_2027_staging_manifest_20261104.json`, kesemua rekod `production_ready=false`.

## Perkara sudah diuji secara statik

- Tahun 4–6 PJ: 101/101 ID PdP muncul dalam indeks SK/SP; semua set SK/SP serupa dengan RPT negeri Johor v57. Semua kod SP ditemui dalam dokumen DSKP tahun yang sepadan (semakan kehadiran kod sahaja, bukan pengesahan semuka lengkap). Satu isu pautan Year 6 PdP 033.
- Tahun 3 PJ: 38/38 PdP struktur, SK dan SP mempunyai hubungan kod yang konsisten; kod SP wujud dalam teks DSKP Tahun 3. Fail draf diwujudkan 001–038.
- Tahun 2 PJ: 37 asal dan 4 akuatik mempunyai kod SP DSKP dan padanan awalan SK; **empat akuatik bukan pelajaran diluluskan**.
- Tahun 2/5 PK: 21 fail dihasilkan daripada rekod editorial sebelum ini; status `production_ready=false` dikekalkan dalam sumber. **ID sumber bukan nombor Lesson**.
- Tahun 3 PK: 9 RPH calon berdasarkan SK 1.1–9.1 dalam DSKP T3, termasuk SK 5.1 pengurusan konflik yang tidak kelihatan sebagai kod eksplisit dalam teks RPT 2026; tiada ID PdP 2027 diandaikan.
- Tahun 4, 5 dan 6 PK: tambahan 27 draf tematik berpandukan sembilan bidang SK setiap tahun. Ia bukan lesson plan tahunan yang sudah disusun mengikut RPT.
- **31** rujukan halaman buku teks PJ Tahun 4–6 masih bertanda belum disahkan dalam RPT staging (jangan isi nombor secara anggaran).

## Punca gerbang tidak boleh diluluskan

1. Dokumen Kurikulum KP2027 Tahun 1 belum diperoleh sebagai sumber yang disahkan; rujukan KSSR Tahun 1 bukan pengganti.
2. PK T2 memerlukan penggabungan/penyelesaian sumber bertindih dan identiti PdP tahunan; PK T3–T6 sudah mempunyai beberapa draf tematik tetapi **masih memerlukan pemetaan sumber ke RPT berurutan** dan penjanaan semua Lesson khusus.
3. Setiap RPH perlu penilaian aktiviti guru/murid yang khusus, pentaksiran/PBD yang boleh dilaksanakan, pematuhan keselamatan (termasuk akuatik), serta penyesuaian dengan konteks tempatan.
4. Tarikh PdP guru mesti dipadankan jadual sekolah dan negeri; slot minggu calon tidak sama dengan jadual sebenar.
5. Pemeriksaan **Word A4 satu halaman**, penjanaan Telegram sebenar dan ujian Web staging belum dijalankan untuk 201 draf. Jangan aktifkan mana-mana fail sebagai RPH READY hanya kerana fail wujud.
6. Sebelum migrasi DB: backup versi baharu, semak integrity/FK/orphan/duplicate dan revalidate status per PdP; tiada reset atau overwrite ke DB lama.

## Keputusan
**PR #169 kekal Draft.** Tiada data baharu diaktifkan pada Telegram, Web, database atau pengguna. Hanya versi draf tersedia untuk audit dan pembetulan seterusnya.

Rujukan prinsip KP2027: [kerangka rasmi KPM](https://www.moe.gov.my/kurikulum-persekolahan-2027) dan [laporan portal Malaysia MADANI mengenai Alam dan Manusia](https://malaysiamadani.gov.my/2025/11/kpm-perkenal-subjek-alam-dan-manusia-kepada-murid-tahap-1-sesi-2027/).
