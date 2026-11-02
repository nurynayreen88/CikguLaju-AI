# Audit sumber bahan Telegram → Web (2026-11-02)

**Skop:** pemeriksaan metadata repository `main` sahaja; **bukan** bukti kelulusan bahan dalam database Telegram aktif.

## Penemuan
- `web/telegram_curriculum_api.py`: endpoint `/internal/curriculum/v1/approved-materials` sengaja memulangkan HTTP 503; belum ada resolver rekod bahan diluluskan.
- `books/english/` mempunyai PDF pecahan buku Student Book/Workbook, termasuk Y1–Y2, Y3, Y4 dan Workbook Y5–Y6. Nama fail hanya membuktikan kewujudan aset dalam repository, **bukan** padanan lesson atau kelulusan.
- `materials/english/year2/lesson_082_speaking_cards.md` wujud; kelulusan dan status penghantaran belum disahkan.
- `web/download_release_gate.py` pada staging memerlukan approval verified, durable idempotency, replay, parity dan trial policy sebelum muat turun awam.
- `/api/materials` kini meminta sumber Telegram dengan autentikasi. Fail dan pautan yang belum disahkan tidak dihantar ke browser.

## Langkah verifikasi wajib sebelum membolehkan muat turun
1. Kenal pasti jadual kelulusan dan rekod lesson di **DB aktif runtime**, bukan berdasarkan nama fail GitHub.
2. Padankan setiap rekod dengan jenis bahan, versi, rujukan buku/halaman/audio, lokasi fail yang boleh dicapai server, checksum, status kelulusan dan keizinan pengguna.
3. Buat resolver read-only Telegram yang menolak rekod tiada, pendua, belum diluluskan atau laluan tidak selamat.
4. Buat delivery server-side dengan pengesahan akaun, hak akses, dan ledger penggunaan yang tahan retry; uji Word/PDF, buku, workbook dan audio.
5. Jalankan ujian Telegram ↔ Web untuk lesson yang sama, termasuk fail hilang dan 503; barulah aktifkan `download_enabled`.

**Larangan:** jangan menganggap aset di GitHub sudah diluluskan; jangan pindah atau reset DB; jangan cipta URL download terus kepada fail private.
