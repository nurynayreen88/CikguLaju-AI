# Pendidikan Islam 2027 — audit PDF dan Jawi 696 RPH (5 November 2026)

**STAGING ONLY / DRAF, bukan FINAL READY.**

## Ujian eksport keseluruhan
- 696/696 fail DOCX berjaya ditukar kepada PDF sebenar menggunakan LibreOffice headless.
- 696/696 PDF mempunyai tepat 1 halaman, saiz A4 potret, teks tidak kosong serta tajuk `RPH STANDALONE`.
- 0 kotak teks PDF melimpah sempadan fizikal halaman mengikut pengukuran PyMuPDF.
- 0 aksara Unicode U+FFFD dalam teks PDF yang diekstrak.
- 35/35 fail berstatus semakan/ditahan juga lulus satu halaman A4; ia **tidak** mengubah status kandungan.
- Semakan visual sampel: T2 L035, T6 L006/L060/L117 dan T5 L134. Baki 691 belum dibaca secara visual satu per satu.

## Fon Jawi/Arab dan tafsiran
- 696/696 PDF mempunyai span Jawi/Arab; median saiz span Jawi/Arab = **11pt** untuk setiap fail dalam pengukuran ini.
- Penanda awal 54 dokumen dengan median keseluruhan <9pt ternyata melibatkan campuran tajuk/nota Rumi 8–8.5pt; **jangan salah klasifikasi sebagai 54 kegagalan fon Jawi**.
- Pengukuran fon/ekstrak teks tidak menjamin setiap glyph dan penjajaran benar. Pemeriksaan cetak sebenar masih perlu sebelum READY.

## Gerbang keselamatan
- Enam fail ditahan tidak berubah: T2 L035, T6 L006/L014/L018/L060/L117.
- 29 fail keutamaan kekal perlu audit semantik; 661 hanya calon pratonton guru.
- Kesinambungan tasmi' al-Quran, DSKP, aktiviti/PBD, buku teks serta takwim negeri belum disahkan menyeluruh.
- Tiada pengubahsuaian `main`, DB, `app.py`, Telegram, Web atau laluan akses bayaran.

Artefak CSV audit per-Lesson dan laporan terperinci disimpan di folder Library `/CikguLaju/Pendidikan_Islam_2027_STAGING/`; pakej V2 kekal tidak ditindih.
