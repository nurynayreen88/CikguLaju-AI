# CikguLaju English — kekalkan WMA asal (5 November 2026)

**Keputusan pemilik projek:** Fail `.wma` dikekalkan sebagai WMA asal. Keserasian playback telefon **bukan syarat untuk mengekalkan fail**. Jangan tukar nama sambungan, transkod, atau padam fail sumber.

## Bukti kod Telegram sedia ada (audit AST pada app.py)

- Penghantar English Y1–Y2: `_eng12_send_verified_audio` menggunakan fail sementara berakhiran `.wma`, menghantar dengan medan Telegram `document`, nama `.wma`, MIME `audio/x-ms-wma`. Ini ialah laluan asal yang perlu dikekalkan. Semakan ini hanya pengesahan **kod**, bukan penghantaran/live playback.
- Penghantar media umum: `_send_verified_media_rows_v2594` sentiasa mengeluarkan suffix `.mp3` dan MIME `audio/mpeg`, termasuk percubaan ulang `document`. Jangan hantar fail WMA melalui laluan tersebut tanpa pembetulan format bersandarkan identiti sumber.
- Tahun 4 menggunakan Get Smart Plus 4. **24 laluan WMA lama** di bawah Super Minds 1 berkaitan **19 Lesson** mesti ditahan **kerana salah buku**, bukannya kerana jenis WMA. Fail asal kekal di Drive; tiada migrasi atau penghapusan.
- MP3 sumber Get Smart Plus 4 yang bersesuaian dan track TB/SB masih menunggu semakan kandungan audio, sebelum laluan tahan boleh diluluskan secara berasingan.

## Peraturan pelaksanaan

1. Kekalkan media source file ID, nama dan extension asal apabila sumber buku/lesson disahkan.
2. Fail WMA boleh dihantar sebagai **dokumen** `.wma`; jangan menyamar sebagai `.mp3`.
3. Kes sumber salah buku ditahan mengikut ID/lesson dan rujukan TB/SB, **bukan filter `.wma` global**.
4. Jangan auto-lulus audio hanya kerana nama CD/Track sepadan.
5. Jangan ubah `main`, database, kredit, pembayaran, referral, RPH Word/PDF atau Telegram LIVE untuk audit ini.

**Ujian:** `tests/test_english_wma_sender_source_contract_20261105.py` (statik kontrak format), `tests/test_english_y4_wrong_book_audio_hold_20261105.py` (pengasingan sumber dan Tahun 1/2 tidak disekat).

**Status:** AUDIT DAN PERLINDUNGAN DALAM STAGING SAHAJA. Belum ada pengesahan audio didengar atau penghantaran Telegram sebenar.
