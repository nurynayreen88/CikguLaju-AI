# Pendidikan Muzik 2027 — Semakan sumber penerbitan Web–Telegram

Tarikh: 6 November 2026. Bukti konfigurasi Render diperoleh melalui sambungan Render, hanya baca.

| Perkhidmatan | Render service | Cabang auto-deploy | Auto-deploy |
|---|---|---|---|
| Bot Telegram CikguLaju-AI | `srv-dah3b8lbedkc738ugqt0` | `main` | Ya |
| Web pengguna cikgulaju-web | `srv-dbm5go8u01pc738f40cg` | `production/cikgulaju-web-20261105` | Ya |
| Web API ujian lama | `srv-dbjcpsk9v7es739o39a0` | `staging/cikgulaju-web-v1` | Tidak |

## Keputusan

**PR #335 ke `main` tidak boleh digabungkan bersendirian sebagai penerbitan MUZIK.** Ini akan mencetuskan aliran auto-deploy Telegram tetapi bukan cabang produksi Web. Subjek sama berpotensi mempunyai data/format berlainan di kedua-dua platform. Kejayaan GitHub Actions pada PR #335 hanya membuktikan penghasilan fail asas, bukan parity laluan sebenar.

## Gerbang sebelum pengaktifan

1. Tetapkan bahan RPH/RPT teks sahaja sebagai skop; **tiada audio rasmi** dilampirkan atau dihantar kerana tiada bukti hak edaran.
2. Sahkan semakan kurikulum dan skor/notasi serta 81 kriteria kejayaan. Kekalkan 8 PdP pengukuhan sebagai **cadangan**, bukan projek rasmi.
3. Jalankan laluan sebenar penjana RPH pada calon pelepasan Web dan Telegram menggunakan **satu versi fail sumber + digest sama**. Jangan mengambil sumber sandaran senyap.
4. Pastikan kedua-dua cabang mempunyai adapter MUZIK yang sama (SK/SP, masa, kelas, tarikh, nota, Word/PDF). Uji 35 PdP × 5 tahun dan pengesahan entitlement, kuota, pembayaran, referral tanpa mengubah rekod pengguna.
5. Kunci urutan release atau penggunaan feature flag yang sama pada dua platform, dan audit kedua-dua commit telah terpasang di Render sebelum menu MUZIK ditunjukkan kepada pengguna.
6. Pastikan PdP06 dan PdP19 menggunakan slot anjal untuk 2027; tiada andaian tarikh mengajar kelas sebenar.

**Status kini:** fungsi cetakan Word/PDF staging telah lulus, tetapi pelepasan kepada pengguna belum mendapat bukti parity/kelulusan kurikulum lengkap. **Belum FINAL READY / jangan merge atau deploy.**

Laman rujukan:
- [PR Muzik #335](https://github.com/nurynayreen88/CikguLaju-AI/pull/335)
- [CI Muzik 2027](https://github.com/nurynayreen88/CikguLaju-AI/actions/workflows/pendidikan-muzik-2027-staging.yml)
- [Render Telegram](https://dashboard.render.com/web/srv-dah3b8lbedkc738ugqt0)
- [Render Web pengguna](https://dashboard.render.com/web/srv-dbm5go8u01pc738f40cg)
