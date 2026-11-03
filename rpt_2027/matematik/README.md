# RPT Matematik 2027 v28 — PDF Telegram (DRAF/SEMENTARA)

Lima PDF telah disahkan dalam folder Google Drive pemilik, tetapi **tidak**
diterbitkan sebagai pautan muat turun awam. Fail tidak disalin ke repositori
GitHub yang bersifat public.

Sumber PDF asal: [Folder RPT Matematik 2027 — PDF Telegram v28](https://drive.google.com/drive/folders/1UARWx990NzWRJQnPNBJiBYhpfKbZmyOr)

| Tahun | Halaman yang dilaporkan | Nama fail tepat |
|---|---:|---|
| 2 | 21 | `RPT_Matematik_Tahun_2_2027_v28_SEMENTARA.pdf` |
| 3 | 31 | `RPT_Matematik_Tahun_3_2027_v28_SEMENTARA.pdf` |
| 4 | 34 | `RPT_Matematik_Tahun_4_2027_v28_SEMENTARA.pdf` |
| 5 | 32 | `RPT_Matematik_Tahun_5_2027_v28_SEMENTARA.pdf` |
| 6 | 33 | `RPT_Matematik_Tahun_6_2027_v28_SEMENTARA.pdf` |

Versi v28 mengandungi 44 minggu dan penomboran Lesson 001–117 mengikut
laporan penyediaan. **Belum ditanda FINAL VERIFIED.** Rujukan DSKP/buku teks,
buku aktiviti, RPT induk 2027 dan padanan RPH memerlukan audit terakhir.

## Pemasangan selamat (belum dilaksanakan dalam produksi)

1. Letakkan **semua** PDF secara persendirian di direktori pada pelayan
   Telegram; kekalkan nama fail tepat. Jangan jadikan direktori atau fail
   boleh diakses melalui URL tanpa semakan langganan.
2. Tetapkan `CIKGULAJU_RPT_MATH_PDF_DIR` kepada direktori tersebut. Jika tiada,
   modul cuba direktori `rpt_2027/matematik/`; tiada sandaran ke Drive.
3. Dalam laluan WSGI opt-in `tools/run_telegram_with_curriculum_api.py`,
   modul English RPT memaparkan butang Matematik **hanya** jika PDF tahun
   berkenaan wujud dan melepasi semakan header/saiz. Modul Matematik
   menggunakan callback `rpt2027_math_pdf_<tahun>`.
4. Klik muat turun menyemak `_is_admin`/`_access_info(...).active` sekali lagi
   sebelum menghantar PDF melalui `send_document`, dan mengesahkan kejayaan
   respons Telegram. Tiada kredit RPH ditolak.
5. **Nota kritikal:** `Procfile` produksi masih `gunicorn app:app`; laluan
   WSGI opt-in tidak aktif secara automatik. Uji fungsi dan pemasangan fail
   secara berasingan di staging sebelum pertimbangkan pengaktifan.
   Jangan terus menukar start command kerana WSGI opt-in yang sama turut
   mendaftarkan beberapa integrasi lain.

## Keadaan fail / kegagalan

- Tiada PDF atau fail terlalu kecil/tidak berheader PDF: butang tersembunyi
  dan cubaan callback lama gagal dengan mesej yang jelas.
- Akaun belum berbayar: akses ditolak walaupun callback dibina sendiri.
- Nombor tahun lain: tidak dibenarkan.
- Respons Telegram gagal: tidak melaporkan penghantaran berjaya.
- Tiada perubahan kepada database pengguna, kurikulum, RPH, kuota atau
  bot produksi. Fail PDF kekal dalam Google Drive pemilik sehingga mekanisme
  penyimpanan persendirian disediakan.
