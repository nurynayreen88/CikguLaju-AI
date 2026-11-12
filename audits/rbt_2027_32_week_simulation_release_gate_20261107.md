# RPT RBT 2027 Tahun 4–6 — 32 PdP simulasi minggu Kumpulan A/B

**7 November 2026 — STAGING DRAF, bukan RPT sekolah diluluskan.**

## Sebab simulasi berasingan

RPT sumber RBT untuk Tahun 4/5/6 mempunyai 32 PdP per tahun dan tidak menyimpan tarikh/minggu sah bagi 96 PdP. Mengisi tarikh 2027 secara automatik akan mencipta jadual mengajar palsu. Penjana lalai 21 RPT dalam PR #441 oleh itu **kekal tanpa tarikh untuk RBT**.

Tiga PDF tambahan merupakan **simulasi editorial** bagi memudahkan guru menilai format dan susunan:
- 32 PdP `RBT T4`, `RBT T5`, `RBT T6`, setiap satu 60 minit;
- anggap **satu PdP setiap minggu** mulai **M03 hingga M34** (32 minggu berturutan);
- julat minggu A/B diambil *tepat* daripada `rpt_2027/common/calendar_week_2027_a_b_snapshot_20261107_DRAF.json` (44 minggu berjadual/kumpulan);
- **bukan pengesahan hari atau tarikh kelas**: cuti negeri, cuti gantian, kelas sebenar, tempoh projek dan kelulusan sekolah berbeza;
- label setiap minggu: **Mxx (SIMULASI)** dan lajur catatan: **SIMULASI SAHAJA**;
- dipisah ke `staging/rpt_2027_seragam_2026/rbt_32week_SIMULASI/` daripada 21 PDF utama;
- nota sumber asal dikekalkan dalam rekod `source_note`. CSV/RPH asal, DB, Web dan Telegram **tidak diubah**;
- `start_week` boleh ditentukan secara terkawal, tetapi tidak boleh melebihi minggu 44 untuk 32 PdP.

## Semakan DSKP penuh

Audit [16 SK dan 114 SP padanan kod berserta pernyataan](rbt_y4_y6_dskp_full_standard_text_audit_20261107.md) daripada sumber DSKP asal (T4: 8 SK / 57 SP; T5: 5 / 34; T6: 3 / 23). Semakan ialah *teks berturutan* selepas penormalan sengkang PDF, bukan kelulusan visual/mutu pedagogi.

## Hasil ujian dan persembahan

- GitHub Actions: https://github.com/nurynayreen88/CikguLaju-AI/actions/runs/42314765817 — **PASS**.
- Artifak 21 PDF asal + 3 PDF simulasi + imej pratonton:
  https://github.com/nurynayreen88/CikguLaju-AI/actions/runs/42314765817/artifacts/13549938492
- Semua 3 simulasi PDF lulus ujian 32 PdP, padanan A/B tepat pada minggu sumber, pemeliharaan SK/SP, **tiada perubahan sumber**, had minggu sah, muka depan minimum dan teks amaran.
- Pemeriksaan rupa visual halaman kedua RBT T4 dan T6: susunan lima lajur kemas, 5 PdP muat pada halaman, tiada teks terpotong; nota simulasi diringkaskan tanpa menghilangkan nota asal.
- Kalendar masih mempunyai persoalan kelulusan cuti negeri; PDF hanya memaparkan minggu yang dijadualkan, bukan hari PdP sekolah.

## Pagar release

- **96/96 RBT masih belum mempunyai tarikh kelas sebenar disahkan.**
- Buku teks T5–6 dan aktiviti/halaman perlu semakan visual individu; status belum READY.
- RPT 2026 Tahun 4–6 dari portal panitia sekolah:
  https://sites.google.com/moe-dl.edu.my/teduristopcenter/kurikulum/pengurusan-panitia/panitia-reka-bentuk-teknologi
  hanya rujukan **urutan/format**, **bukan** rujukan automatik tarikh tahun 2027.
- RPT simulasi **tidak boleh disajikan sebagai RPT rasmi** atau dimasukkan ke laluan muat turun pengguna sehingga sekolah/guru meluluskan agihan; kekalkan PR #441 sebagai draf.

