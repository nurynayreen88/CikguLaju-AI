# Pendidikan Islam 2027 — checkpoint STAGING (5 November 2026)

**Keputusan: DRAF / BELUM READY.** Cabang ini untuk audit sahaja. Jangan merge, deploy Render, ubah data pengguna, atau aktifkan penghantaran RPH Pendidikan Islam kepada pengguna.

## Inventori dan integriti

- Tahun 2: 112 RPH; Tahun 3: 147; Tahun 4: 151; Tahun 5: 143; Tahun 6: 143.
- **696/696** nombor Lesson wujud secara tepat sekali; tiada pertindihan antara 661 fail pratonton dan 35 fail semakan admin.
- **696/696** DOCX melepasi integriti ZIP dalaman, mempunyai tetapan halaman A4 dalam XML, dan penanda RTL/Jawi dalam XML. Ini tidak membuktikan kesahihan isi.
- 5 RPT Word dari sumber QA v4 turut dimasukkan dalam pakej audit terkawal, tanpa menulis ganti RPT PDF pada `main`.
- 5 RPH sampel (T2 L001; T3 L060; T4 L079; T5 L134; T6 L117) berjaya dirender kepada satu halaman A4. **691 fail belum disemak secara visual dalam checkpoint ini.**
- Bahan asal berasal daripada arkib v4 bertarikh 4 November dan pakej 661/35 yang telah diasingkan. Kandungan teks RPH dan RPT tidak diedit automatik dalam checkpoint ini.

## Pengasingan yang wajib dikekalkan

| Kategori | Jumlah | Pengendalian |
|---|---:|---|
| `CALON_UJIAN_GURU_DRAF` | 661 | Pratonton guru secara terkawal sahaja selepas semakan akses |
| `SEMAKAN_KEUTAMAAN` | 29 | Pemeriksaan sumber dahulu; jangan hantar sebagai READY |
| `TAHAN_SEMAKAN_KANDUNGAN` | 6 | Jangan disalurkan kepada pengguna |

6 fail ditahan ialah **Tahun 2 L035** dan **Tahun 6 L006, L014, L018, L060, L117**. Senarai 29 fail semakan keutamaan ada dalam manifest JSON bersebelahan.

## Baki halangan semantik

1. Tasmi' al-Quran: pertindihan al-Baqarah 224 pada T2 L032/L035; julat calon asy-Syura dan beberapa jurang/akhir surah pada Tahun 3–6. **Jangan mereka ayat atau melengkapkan julat tanpa bukti sumber.**
2. Semakan DSKP dan buku teks secara makna untuk setiap SK/SP, objektif, aktiviti dan PBD **belum selesai**; padanan kod teks semata-mata tidak memadai.
3. DSKP Tahun 3–4 mempunyai batasan pembacaan PDF dalam audit terdahulu. Semak dokumen asal secara visual bagi kod yang meragukan.
4. Semua 696 halaman perlu semakan fon Jawi/Arab selepas cetak PDF dan Word sebenar, bukan hanya struktur XML.
5. Jadual sekolah 2027 mengikut negeri, cuti tambahan, dan laluan Telegram/Web mesti diuji dalam staging sebelum pengeluaran.

## Fail terhasil

`CIKGULAJU_PI_2027_T2_T6_696_RPH_5_RPT_STAGING_20261105.zip`
mengandungi 696 RPH Word yang disusun mengikut status, 5 RPT Word, audit CSV per-Lesson serta laporan dan data tasmi' terdahulu.

Arkib disimpan sebagai artefak staging berasingan; ia **tidak dimasukkan ke GitHub main** dan tidak mengubah salinan produksi. Manifest JSON di repo ini ialah checkpoint yang boleh diuji dan tidak mengaktifkan pembaca Telegram.

## Dasar keselamatan

- **Tiada** perubahan terhadap `app.py`, database `v26.00`, fail PDF RPT yang sudah ada, kelulusan bayaran, akaun pengguna, Telegram atau Web.
- Label `DRAF`/isu sumber pada fail asal dipelihara.
- Lulus format/ZIP bukan bukti `FINAL READY`.
