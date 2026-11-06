# Pendidikan Muzik 2027 — Release Gate Semasa (6 November 2026)

**Keputusan:** STAGING DRAF, **BUKAN FINAL READY**. Tidak dibenarkan merge/deploy tanpa kelulusan baharu. Tiada perubahan kepada main, Supabase, bot, Web, pembayaran, kredit percuma atau referral.

## Status bukti yang telah diselesaikan

| Komponen | Bukti | Status |
|---|---|---|
| RPH Tahun 2–6 | 175 fail / 35 setiap tahun | **DRAF lengkap** |
| Semakan isi buku/projek | 167/175 pada skop semakan terhad | **Tidak sama dengan kelulusan penuh** |
| Aktiviti pengukuhan guru | 8/8 mempunyai aktiviti khusus | **Bukan Projek Muzik 3 rasmi** |
| Kriteria kejayaan | 94 sumber asal + 81 sidecar khusus | **81 masih draf editorial** |
| RPT 2027 | 5 CSV dan MD | **DRAF** |
| Padanan minggu induk A/B | 175/175 sama dengan snapshot | **Lulus indeks, belum hari negeri** |
| Pemetaan format RPH native | 175/175 lulus ujian fasa | **Pratonton staging sahaja** |
| Identiti fail sumber | 175/175 SHA-256 dari lima fail; mutation/symlink ditolak | **Lulus kawalan fail, bukan kelulusan isi** |
| Word fungsi asas Telegram | 175/175 dijana, setiap satu 3 jadual | **Lulus ujian asas** |
| Word dirender LibreOffice | 175/175 **1 halaman A4** | **Lulus ujian asas** |
| PDF fungsi asas Telegram | 175/175, **1 halaman A4** dan kod SP/aktiviti tidak gugur | **Lulus ujian asas** |
| Contoh Word/PDF untuk manual QA | 5 pasang + nota DRAF | **Tersedia dalam artifact GitHub** |

Bukti CI terkini:
- [Larian 42133072447](https://github.com/nurynayreen88/CikguLaju-AI/actions/runs/42133072447), semua ujian lulus.
- [Muat turun lima pasangan contoh semakan](https://github.com/nurynayreen88/CikguLaju-AI/actions/runs/42133072447/artifacts/13464850773).
- [Laporan JSON 175 janaan](https://github.com/nurynayreen88/CikguLaju-AI/actions/runs/42133072447/artifacts/13463868059).

**Had metodologi:** Ujian Word/PDF mengekstrak fungsi asas `app.py` secara AST tanpa mengimport bot, DB atau rangkaian adapter produksi. Halaman Word diukur dengan LibreOffice dalam runner GitHub, bukan disahkan dalam Microsoft Word semua versi. Kemenangan CI **bukan** bukti keseluruhan laluan sebenar Telegram–Web sudah menyokong Muzik.

## Sekatan sebelum FINAL READY

1. **Kurikulum Tahun 4:** PdP21 dan 24 mempunyai kod lama `3.1.x`, sedangkan DSKP/buku mencetak `3.2.x` di bawah SK 3.1. Selain itu SK 4.1/SP4.2.1 dan skop not B/A/G berbanding G/A/B/C’ memerlukan keputusan berautoriti. Jangan ubah senyap. Rujuk `year4/AUDIT_SK_SP_DSKP_BUKU_20261106.md`.
2. **Skor/notasi muzik:** belum semuanya disemak secara visual dan dibuat padanan kepada perincian aktiviti; semakan teks/Word tidak mengesahkan not pada skor.
3. **Audio:** nombor Audio bercetak tidak mengesahkan fail audio, padanan track atau hak penggunaan. Tiada lagu/fail audio diaktifkan dalam sistem Muzik dan `source_book_audio_file_verified=false` untuk rekod yang berkaitan.
4. **Tarikh sekolah negeri:** slot minggu A/B lulus, tetapi cuti perayaan/gantian/negeri serta hari sebenar jadual kelas belum diaudit satu-persatu bagi Muzik.
5. **81 kriteria kejayaan:** sediakan 81 calon khusus, tetapi perlu semakan pedagogi terhadap objektif, kemahiran dan PBD sebelum menyerap ke fail utama yang diluluskan.
6. **8 pengukuhan cadangan:** kekalkan label bukan rasmi; jangan pernah cipta projek 3 atau tuntut halaman buku teks khusus.
7. **Pengaktifan Web/Telegram:** subjek MUZIK masih tiada dalam `web/native_rph_telegram_api.py` dan `web/rph_shared_source_identity.py`; ujian hanya menggunakan allowlist dalam namespace sementara dan fail identiti staging. Tiada parity penuh runtime atau ujian entitlement.
8. **Semakan manual dokumen:** lima pasang contoh telah disediakan untuk pemeriksaan ahli kurikulum / pemilik projek; hasilnya belum diberi sign-off.

**Syarat penerbitan:** semua sekatan di atas diputuskan dan direkod, sumber sama digunakan pada Web/Telegram, kemudian CI baharu serta ujian sebenar pengguna staging lulus; barulah PR boleh dipertimbangkan untuk merge mengikut aliran terkawal.


## 6 November 2026 — 10 PdP RPT 2027 perlu penjadualan anjal
- Indeks hari sebenar 16 negeri × 365 hari (5,840 rekod) menunjukkan **M06/PdP06** dan **M19/PdP19** adalah **0 hari calon PdP** bagi semua 16 negeri, mengikut status kalendar bertarikh pembekuan 28 Okt 2026.
- **10 PdP unik (2 × 5 tahun)** diberi penanda `rpt2027_day_audit` dalam manifest; RPT CSV dan Markdown menerima amaran. **Tiada minggu, tarikh slot, kod SK/SP atau susunan PdP diubah.** Guru mesti sahkan hari sebenar melalui jadual dan negeri. Rujuk `KALENDAR_2027_HARI_PDP_NEGERI_AUDIT_20261106.md`.
- Data sumber merujuk hari **calon** dan boleh berubah mengikut pengumuman KPM/warta; ini bukan kelulusan automatik RPT atau perubahan produksi.


## 6 November 2026 — Audit kod SP Tahun 2–6 lengkap
- **173/175 RPH** menggunakan nombor SP yang dijumpai dalam teks DSKP Muzik bagi tahun yang sama; **2 pengecualian Y4 PdP21/24** menggunakan `3.1.x` yang tiada dalam DSKP Muzik Y4 tetapi `3.2.x` tercetak. Semakan ini **kod sahaja**, bukan makna, notasi, skor atau kelulusan.
- Cadangan kod DSKP/BT terpisah dari `manifest_sp`, tanpa menukar nilai asal. Lihat `DSKP_SP_CODE_PRESENCE_175_20261106.json` dan `DSKP_SP_CROSSWALK_AUDIT_20261106.md`. Gate release tetap tertutup.


## 6 November 2026 — Ujian kandungan Word/PDF dan pembetulan Unicode di staging
- Semakan ketat awal menemui isu `clean_doc_text` pada penjana asas Telegram: tanda `–`/`—` hilang sehingga `4–5` menjadi `45`; **78/175** dokumen mencetuskan ralat perbandingan medan dalam ujian pertama.
- Adapter `legacy_doc_text_safe_staging.py` kini mengekalkan makna tanda baca, contohnya `4–5` → `4-5`, atau **menolak aksara lain yang tidak dapat dikendalikan** (fail closed). **175/175 Word dan PDF lulus semula**, setiap satu halaman A4, dengan 4 medan pedagogi dikekalkan bagi kedua-dua format. Bukti [Actions 42138313500](https://github.com/nurynayreen88/CikguLaju-AI/actions/runs/42138313500) dan [uji skop PR 42138320014](https://github.com/nurynayreen88/CikguLaju-AI/actions/runs/42138320014).
- **Adapter ini belum disambungkan ke runtime Web/Telegram**, maka pembetulan Unicode untuk dokumen pengguna masih release blocker. Jangan ubah `app.py` atau subjek lain melalui PR Muzik.
- Audio: [AUDIO_MEDIA_ACCESS_RIGHTS_20261106.md](AUDIO_MEDIA_ACCESS_RIGHTS_20261106.md) merekod bukti buku/DVD dan larangan menyangka fail/lesen sudah diperoleh. Tiada fail/URL audio dihantar kepada pengguna.
