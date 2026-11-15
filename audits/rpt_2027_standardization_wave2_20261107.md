# RPT 2027 — Gelombang 2, susun atur seragam (7 Nov 2026)

**Status: PR #441 DRAF, STAGING. Bukan keluaran untuk Telegram atau Web.**

## Hubungan dengan gelombang pertama

PR #440 telah digabung ke main sebagai *penjana dan ujian*, bukan pengganti RPT pengguna. Gelombang pertama merangkumi 13 PDF pratonton: PSV T2–6 (42 PdP x5), RBT T4–6 (32 PdP x3), Moral T2–6 (96 sesi x5).

Gelombang kedua menggunakan penjana yang sama dan memperuntukkan 8 lagi PDF untuk audit:

| Subjek | Sumber input sedia ada | Tahun | Rekod sumber | Nota penting |
|---|---|---|---:|---|
| Sejarah | `rpt_2027/sejarah/RPT_SEJARAH_TAHUN_{year}_2027_A_B_DRAF.csv` | 4–6 | 36/tahun (108) | Julat tarikh A/B calon; halaman buku dalam CSV ialah **julat unit**, bukan bukti aktiviti individu |
| PJPK | `rpt_2027/pjpk/pjpk_2027_rpt_manifest.json` | 2 | 37 PJ + 35 PK (72) | Dua urutan PdP mesti dipaparkan berasingan |
| PJPK | Manifest sama | 3 | 38 PJ + 32 PK (70) | Aktiviti/PBD sumber dinyatakan hanya jika wujud |
| PJPK | Manifest sama | 4 | 34 PJ + 32 PK (66) | Pisahkan unit/tajuk PJ daripada field asal jika bercantum |
| PJPK | Manifest sama | 5 | 33 PJ + 32 PK (65) | Cuti negeri/gantian belum disahkan |
| PJPK | Manifest sama | 6 | 34 PJ + 32 PK (66) | Cuti negeri/gantian belum disahkan |

**Jumlah sasaran:** 8 PDF tambahan, 447 baris PdP; 21 PDF / 1,233 baris PdP merentas kedua-dua gelombang, jika semuanya lulus CI.

## Peraturan pemetaan dan pagar release

- **PdP, bukan minggu**, ialah identiti kandungan. Sejarah menggunakan ID sumber `SEJ-T*-PDP-NNN`; PJPK memaparkan label sebenar `PJ PdP NNN` atau `PK PdP NNN`. Nombor baris dalaman PDF tidak menggantikannya.
- Tarikh 2027 datang terus daripada CSV/manifest, atau ditinggalkan kosong jika sumber tiada. Semua tarikh tersebut masih **cadangan**; semak takwim KPM, negeri dan cuti gantian sebelum release.
- Susunan 5 lajur A4 landskap: Minggu/Tarikh; Unit/Tajuk/PdP; SK; SP; Catatan/Bahan.
- SK/SP dan aktiviti guru/murid dipaparkan **setakat yang ada dalam sumber**. Penjana tidak menokok tambah aktiviti apabila sumber kosong.
- Halaman buku teks Sejarah ialah **julat unit**, bukan pengesahan aktiviti. Jangan jadikan status bukti halaman sama dengan kelulusan RPH.
- Perubahan hanya pada penjana staging, ujian dan CI; tiada perubahan fail PDF aktif, DB, `app.py`, Web atau Telegram.
- Semakan visual bagi contoh setiap tahun serta kelulusan kandungan PdP masih wajib. CI lulus bukan tanda `FINAL READY`.

## Baki jurang untuk gelombang berikutnya

- BM T2–6: struktur 5 lajur sudah wujud, tetapi HTML memaksa 1 minggu = 1 muka surat; perlu adapter sumber PdP yang mengalir merentas halaman.
- Matematik T2–6: hanya PDF sementara, perlukan sumber PdP tersusun bagi mengelak rekonstruksi PDF tanpa bukti.
- Pendidikan Islam T2–6: perlukan adapter struktur dan QA font Jawi/Arab/RTL.
- English T2–6: jadikan PDF aktif sebagai contoh visual, bukan bukti kesahan semua Lesson.
- Bahasa Arab T2–6: indeks PdP DRAF ada; nombor unit/fokus dan font Arab mesti melalui QA RTL, tarikh PdP masih kosong.
- Muzik T2–6, Sains T2–6: perlu perakuan sumber berstruktur dan pemetaan DSKP/kurikulum sebelum penerbitan.
- Tahun 1 KP2027: **audit kurikulum baharu berasingan**; jangan salin RPT KSSR T2–6.

**Keputusan:** PR #441 mesti kekal DRAF dan tidak di-merge/deploy atas QA struktur semata-mata.
