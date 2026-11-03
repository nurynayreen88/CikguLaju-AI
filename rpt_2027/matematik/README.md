# RPT Matematik 2027 v28 — Muat turun Telegram (DRAF/SEMENTARA)

Ini menggunakan **kaedah yang sama dengan RPT English 2027**:
lima PDF disimpan terus dalam folder `rpt_2027/matematik/` dan
`telegram_downloads.py` menghantar fail melalui `send_document()`.
Tiada muat naik atau bacaan PDF daripada Supabase; tidak perlu
konfigurasi environment variable atau pemasangan fail manual di Render.

| Tahun | Halaman | Fail PDF |
|---|---:|---|
| 2 | 21 | `RPT_Matematik_Tahun_2_2027_v28_SEMENTARA.pdf` |
| 3 | 31 | `RPT_Matematik_Tahun_3_2027_v28_SEMENTARA.pdf` |
| 4 | 34 | `RPT_Matematik_Tahun_4_2027_v28_SEMENTARA.pdf` |
| 5 | 32 | `RPT_Matematik_Tahun_5_2027_v28_SEMENTARA.pdf` |
| 6 | 33 | `RPT_Matematik_Tahun_6_2027_v28_SEMENTARA.pdf` |

Semua dokumen mempunyai 44 minggu dan Lesson 001–117.
**Ini v28 DRAF/SEMENTARA, bukan FINAL VERIFIED.**
Rujukan halaman buku teks/buku aktiviti dan padanan semua RPH
standalone belum disahkan sepenuhnya.

Fail asal diambil daripada [folder Google Drive pemilik](https://drive.google.com/drive/folders/1UARWx990NzWRJQnPNBJiBYhpfKbZmyOr).
Ujian integriti SHA-256 fail PDF dijalankan dalam CI.

## Telegram dan akses

Bot menggunakan aliran sedia ada `RPT 2027 → Tahun → Matematik (PDF)`
untuk Tahun 2–6. Hanya pengguna dengan akses berbayar aktif,
Rakan Pembangun disahkan, atau admin boleh memuat turun melalui
Telegram; callback muat turun menyemak hak akses semula.
Tiada kuota percubaan RPH ditolak. Penghantaran diperiksa menerusi
respons Telegram; callback bukan Matematik diteruskan seperti biasa.

**Penting:** repositori GitHub CikguLaju ialah **public**.
Oleh itu PDF ini, seperti PDF English dalam repositori yang sama,
boleh dimuat turun terus dari GitHub tanpa sekatan langganan bot.
Sekatan berbayar hanya melibatkan menu dan penghantaran Telegram.

Kod `private_bundle.py` dan `supabase_assets.py` terdahulu tidak
diperlukan lagi dan telah dikeluarkan dari cabang release ini.
Jadual Supabase yang pernah dibuat dahulu tidak digunakan;
tiada data pengguna atau kurikulum diubah.
