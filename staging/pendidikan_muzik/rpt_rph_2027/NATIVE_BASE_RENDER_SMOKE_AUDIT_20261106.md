# Pendidikan Muzik: ujian cetakan asas Telegram (staging)

Skrip `native_base_render_smoke_staging.py` menggunakan AST untuk **menjalankan fungsi RPH asas yang disalin terus daripada kod semasa `app.py`**, dan fungsi penerimaan input `web/native_rph_telegram_api.py`, dengan pengecualian **allowlist Muzik yang hanya wujud dalam namespace ujian**.

Sebab tidak import `app.py`: fail tersebut menjalankan bootstrap database apabila diimport; skrip mengelakkan risiko sentuhan data, bot, Supabase, bayaran, kredit atau Telegram.

**Batas penting:** Render asas ini **tidak menjalankan keseluruhan rantaian adapter/wrapper runtime produksi**, tidak membuktikan parity identiti sumber Web–Telegram, dan tidak membuktikan Word 1 halaman (DOCX belum di-layout dengan Word/LibreOffice). Ia hanya menguji pembentukan Word dan PDF sebenar menggunakan fungsi asas sedia ada. Jika PDF melebihi satu halaman, ia direkod sebagai kecacatan layout, bukan diubah atau dipotong secara senyap.

Ujian CI bermula dengan 5 contoh berbeza: Tahun 2 PdP 1; Tahun 3 PdP 20; Tahun 4 PdP 21 (konflik SP); Tahun 5 PdP 34 (projek); Tahun 6 PdP 35 (pengukuhan). **Jangan menanda FINAL READY daripada smoke test.** Selepas lulus, jalankan `--all` untuk 175 rekod. Keputusan ujian terakhir mesti dicatat dalam PR sebelum sebarang penerbitan.
