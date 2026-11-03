# Pemeriksaan sebelum integrasi — Matematik Tahun 4 (83 RPH)

**Tarikh:** 3 November 2026. **Keputusan:** BELUM LAYAK DIJADIKAN RPH PRODUKSI. Audit ini tidak mengubah sebarang kod runtime atau DB.

## Aplikasi semasa

- GitHub: `nurynayreen88/CikguLaju-AI`, default `main`.
- Render produksi `CikguLaju-AI`: servis `srv-dah3b8lbedkc738ugqt0`, branch `main`, auto-deploy **yes**, start command `gunicorn tools.run_telegram_with_curriculum_api:app`.
- Deploy terakhir yang disahkan: `4dd14a5` (3 November 2026, status live).
- Runtime wrapper memasang adapter English Tahun 2 dan Tahun 4, serta curriculum API; tidak ada adapter Matematik Tahun 4 yang disahkan melalui wrapper ini.
- `app.py` ialah fail besar; pemeriksaan fail utama secara penuh belum selesai. JANGAN memintas semakan laluan muat turun/generator atau mengubah menu RPH tanpa ujian runtime.

## Semakan fail yang hendak dimasukkan

- Sumber: pakej Word `Matematik_T4_83_RPH_Pakej_v15_PRA_READY.zip`, bukan fail dalam repositori `main`.
- 83 dokumen individu, ID `01–10`, `11A–11C`, `12–81` (tidak ada ID `11` tunggal), semua A4.
- 83/83 masih bertanda **PRA-READY**.
- 77/83 masih menyebut RPT 2026.
- 83/83 menyebut urusan RPT 2027 yang belum selesai.
- 77/83 menyebut Buku Aktiviti belum disahkan.
- 83/83 mempunyai bahagian asas RPH (set induksi, aktiviti, pentaksiran, penutup, BBM).
- Audit teknikal sahaja tidak membuktikan penjajaran semua aktiviti kepada buku dan tarikh kelas, atau kelulusan pedagogi.

## Kawalan sebelum pengaktifan

1. Tuntaskan padanan RPT 2027 dan semak sumber aktiviti/halaman buku pada setiap RPH.
2. Tentukan sama ada 83 Word ini bahan muat turun, sumber generator atau kedua-duanya; kekalkan laluan DB v26.00 dan aliran Telegram/Web asal sehingga siap ujian.
3. Import hanya melalui adapter terasing/opt-in dengan fallback generator lama; jangan mengganti DB atau meminda `app.py` secara terus.
4. Uji Matematik Tahun 4 dan regresi subjek/tahun lain pada staging. Semak fail Word/PDF benar-benar tiba di Telegram dan padanan Lesson/PdP betul.
5. Luluskan secara manual sebelum PR ke `main`, kerana Render produksi auto-deploy pada setiap commit `main`.

## Kesimpulan

**Jangan merge/deploy buat masa ini.** Kod pemeriksaan `tools/check_matematik_t4_package.py` sengaja baca sahaja dan akan menolak pakej ini (`release_allowed = false`). Fail asal, DB, `main` dan Render tidak disentuh.