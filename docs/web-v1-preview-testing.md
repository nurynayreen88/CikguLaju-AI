# Ujian pratonton CikguLaju Web V1

## Skop

Pratonton ini bukan laman production. Ia hanya untuk menyemak reka bentuk dan dropdown Tahun → Subjek → Unit → PdP. Butang Jana RPH sengaja tidak aktif. Jangan kongsi data peribadi atau maklumat murid.

## Jalankan secara tempatan

1. Checkout branch `staging/cikgulaju-web-v1` pada komputer ujian.
2. Pasang Flask: `python -m pip install Flask==3.1.0`.
3. Jalankan `python tools/run_web_v1_preview.py`.
4. Buka `http://127.0.0.1:5055/` pada komputer yang sama.
5. Pilih Tahun; dropdown Subjek hanya aktif selepas Tahun dipilih.

Untuk Unit dan PdP, tetapkan `CIKGULAJU_WEB_PREVIEW_DB` kepada laluan fail SQLite salinan ujian yang mengandungi jadual `rpt_entries`. Akses database menggunakan `mode=ro` dan `PRAGMA query_only=ON`. Jangan gunakan fail production untuk ujian tanpa salinan selamat.

## Pemeriksaan sebelum pautan awam

- Jalankan ujian GitHub Actions `CikguLaju Web V1 isolated checks` sehingga lulus.
- Uji pada telefon: susun atur, sentuhan dropdown, mesej loading/ralat, dan perubahan pilihan.
- Sahkan subjek, unit dan PdP terhadap sumber kurikulum sebenar; rekod RPT bukan bukti RPH standalone tersedia.
- Audit log masuk, CSRF, had kredit dan akses sebelum sebarang penjanaan RPH.
- Jangan mengubah branch `main` atau Render production untuk pratonton.

## Status

Tiada pautan awam pratonton yang telah diterbitkan. Pelayan Flask ini hanya mendengar pada `127.0.0.1:5055`. Pautan ke kod GitHub bukan pautan aplikasi web yang boleh diuji terus.
