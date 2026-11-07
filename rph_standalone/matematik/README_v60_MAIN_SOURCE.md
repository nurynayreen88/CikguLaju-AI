# RPH Matematik v60 — sumber kanonik teks (Tahun 2–6)

**Snapshot kandungan disediakan untuk integrasi ke repositori**. Mengandungi **585 RPH Markdown** (117 Lesson bagi setiap Tahun 2, 3, 4, 5 dan 6), diambil **tanpa pengubahsuaian** daripada ZIP v60.

- ZIP asal: `CIKGULAJU_MATEMATIK_v60_585_RPH_OBJEKTIF_PBD_T4_STAGING.zip`
- Salinan arkib binari Word/PDF (Drive, folder Matematik, akses ikut kebenaran pemilik): https://drive.google.com/file/d/1IoCiTr9P6nRi4rwiMeiIWkfexTJHBmI4/view?usp=drivesdk — **49,194,607 bait**. Ini aset persendirian, bukan fail public GitHub. Aplikasi memerlukan akses sah untuk mengambilnya; jangan anggap ia tersedia secara automatik di runtime.
- SHA-256 ZIP: `a641d7aff88b375f4786807a10eed384d9b6b22fea632d11ad9f2bc97fec5271`
- Pek Tahun 2–6: `v60_source/Tahun_<tahun>.json.zlib.b64.txt`
- `v60_source/manifest.json`: hash setiap pek dan jumlah tepat 117 Lesson
- `v60_source_loader.py`: pembaca **read-only**, semak SHA-256 hingga aras 585 RPH, tiada akses database.
- Ujian: `python -m unittest discover -s tests -p test_matematik_v60_main_source.py -v`

**Cara semak**
```bash
python -m rph_standalone.matematik.v60_source_loader --verify
python -m rph_standalone.matematik.v60_source_loader --lesson 4 14
python -m rph_standalone.matematik.v60_source_loader --export /tmp/rph_matematik_v60_markdown
```

**Had penting:** Snapshot GitHub ini membawa **teks penuh RPH** sahaja, bukan fail Word/PDF binari asal. Untuk Word/PDF tepat satu halaman A4, gunakan ZIP asal dengan checksum di atas (585 Word, 585 PDF individu, lima PDF gabungan). Jangan berpura-pura fail Word/PDF atau loader ini sudah dipasang pada Telegram/Web.

**Kawalan keselamatan:** Tiada import automatik ke `app.py`, database pengguna, Supabase, Render atau sistem pembayaran. Tidak mengubah RPT. Ini tidak mengisytiharkan `FINAL READY` akademik: signoff item buku teks dan E2E Telegram–Web sebenar belum lengkap. Laluan data aktif perlu migrasi *opt-in*, backup dan ujian berasingan. Jangan gunakan fallback senyap ke data tidak disahkan.

**Tujuan pengasingan:** PR terdahulu #444 merangkumi audit, ujian dan kod pratonton sejarah; **snapshot v60 dikomit berasingan daripada PR itu supaya hanya kandungan RPH yang dinyatakan boleh digabung ke main tanpa membawa audit RPT lama.**
