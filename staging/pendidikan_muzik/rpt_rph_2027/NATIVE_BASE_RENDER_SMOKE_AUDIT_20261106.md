# Pendidikan Muzik: ujian cetakan asas Telegram (staging)

Skrip `native_base_render_smoke_staging.py` menggunakan AST untuk **menjalankan fungsi RPH asas yang disalin terus daripada kod semasa `app.py`**, dan fungsi penerimaan input `web/native_rph_telegram_api.py`, dengan pengecualian **allowlist Muzik yang hanya wujud dalam namespace ujian**.

Sebab tidak import `app.py`: fail tersebut menjalankan bootstrap database apabila diimport; skrip mengelakkan risiko sentuhan data, bot, Supabase, bayaran, kredit atau Telegram.

**Batas penting:** Render asas ini **tidak menjalankan keseluruhan rantaian adapter/wrapper runtime produksi**, tidak membuktikan parity identiti sumber Web–Telegram, dan tidak membuktikan Word 1 halaman (DOCX belum di-layout dengan Word/LibreOffice). Ia hanya menguji pembentukan Word dan PDF sebenar menggunakan fungsi asas sedia ada. Jika PDF melebihi satu halaman, ia direkod sebagai kecacatan layout, bukan diubah atau dipotong secara senyap.

Ujian CI bermula dengan 5 contoh berbeza: Tahun 2 PdP 1; Tahun 3 PdP 20; Tahun 4 PdP 21 (konflik SP); Tahun 5 PdP 34 (projek); Tahun 6 PdP 35 (pengukuhan). **Jangan menanda FINAL READY daripada smoke test.** Selepas lulus, jalankan `--all` untuk 175 rekod. Keputusan ujian terakhir mesti dicatat dalam PR sebelum sebarang penerbitan.


## Ujian penuh 175 RPH — GitHub Actions 6 November 2026

**Bukti:** [GitHub Actions run 42129353421 (LULUS)](https://github.com/nurynayreen88/CikguLaju-AI/actions/runs/42129353421) dan [JSON audit dalam artifact GitHub](https://github.com/nurynayreen88/CikguLaju-AI/actions/runs/42129353421/artifacts/13463056172).

| Pemeriksaan asas | Keputusan |
|---|---:|
| Sumber RPH Tahun 2–6 | **175/175** |
| Dokumen Word berjaya dijana | **175/175** |
| Word mempunyai tiga jadual dan halaman seksyen A4 | **175/175** |
| Fail PDF berjaya dijana | **175/175** |
| Fail PDF satu halaman A4 | **175/175** |
| Galat penjana dalam ujian asas | **0** |
| Halaman sebenar Word selepas layout/render aplikasi | **BELUM DIUKUR** |
| Kesamaan generator Telegram/Web penuh, keizinan dan sumber | **BELUM DISAHKAN** |
| Kelulusan SK/SP dan kandungan lagu/audio | **BELUM DISAHKAN** |

Skrip memilih **fungsi asas RPH** secara AST daripada `app.py` (tanpa import/bootstrap DB), bukan keseluruhan chain adapter yang dipasang dalam Telegram LIVE. Python3.11 gagal memproses seluruh `app.py` kerana f-string pada kod lain; ujian menggunakan ekstraksi fungsi terpilih tanpa mengubah aplikasi produksi. Kelulusan CI adalah **smoke test dan ujian struktur dokumen**, bukan final readiness atau kebenaran menjual bahan.

**Langkah menyusul:** periksa Word sebenar selepas conversion untuk mengukur bilangan halaman, banding teks PDF/Word dengan sumber mengikut PdP, lakukan pembetulan SK/SP Tahun 4 melalui semakan kurikulum, aktifkan dan uji source-parity kedua platform hanya setelah kelulusan. Semua sumber staging sahaja.
