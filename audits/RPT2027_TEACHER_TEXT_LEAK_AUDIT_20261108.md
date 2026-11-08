# RPT 2027 — Audit kebocoran nota pembangun ke kandungan guru (8 Nov 2026)

**Status: AUDIT STAGING; pembetulan PDF FINAL belum disahkan. JANGAN MERGE/DEPLOY sebagai FINAL READY.**

## Punca yang disahkan
Nota semakan sumber, status draf dan arahan kerja pembangun telah dimasukkan ke dalam isi, catatan, muka depan atau footer bahan RPT. Contoh sebenar:
- "Pemetaan buku teks belum disahkan; rujuk buku dan DSKP sebelum READY" (dilaporkan dalam RPT Pendidikan Islam T4).
- BM T2: "DRAF UNTUK SEMAKAN: cuti negeri/gantian, SK/SP, aktiviti dan BT/BA masih memerlukan pengesahan menyeluruh", selain "pemetaan PKJR belum disahkan".
- PSV T5: "Pemetaan buku teks belum disahkan".
- RBT T4 CSV: "(calon teks digital; belum sah)" dan "pengesahan guru belum dibuat".
- Sejarah T4–T6 HTML: "STATUS DRAF" berserta nota pengesahan halaman/cuti.
- Matematik T4 Google Drive draf: "PRA-READY", "Buku Aktiviti belum disahkan", "Pengesahan instrumen belum selesai".

## Saringan fail sumber teks (bukan pengesahan PDF)
Saringan pada cabang `feat/rpt2027-sejarah-pjpk-unified-staging-20261107`:
| Fail sumber | Padanan frasa amaran |
| --- | ---: |
| BM HTML T2, T3, T4, T5, T6 | 17, 15, 19, 22, 14 |
| PSV HTML T2, T3, T4, T5, T6 | 2, 2, 2, 3, 2 |
| Sejarah HTML T4, T5, T6 | 1, 1, 1 |
| RBT CSV T4, T5, T6 | 96, 64, 32 |
| Moral CSV A T2, T3, T4, T5, T6 | 0, 0, 0, 0, 3 |

**Definisi:** angka di atas ialah *bilangan padanan regex/frasa*, BUKAN bilangan PdP salah, bukan bilangan dokumen diterbitkan, dan bukan audit seluruh PDF. CSV ialah sumber pembangunan, jadi catatan dalaman dalam CSV dibenarkan **asalkan ia tidak terpapar kepada guru**.

## Cakupan dan had
PR #441 menghuraikan 56 PDF pratayang daripada 12 subjek T2–T6; fail Tahun 1 KP2027 dan menengah bukan dalam kelompok ini. PDF yang hanya tersedia sebagai artifak CI atau binari perlu diekstrak teksnya mengikut halaman. **Jangan dakwa 56 PDF bersih berdasarkan pemeriksaan CSV/HTML ini.**

Audit automatik ditambah:
- `scripts/audit_rpt2027_teacher_text_leaks_20261108.py`: baca semua halaman PDF yang boleh diekstrak dan fail HTML/CSV; lapor nama fail, halaman, frasa dan konteks. Boleh guna `--teacher-output-only` untuk mengecualikan CSV sumber.
- `tests/test_rpt2027_teacher_text_leak_scan.py`: uji frasa amaran dan elak positif palsu seperti "semakan bahan bertulis".
- Workflow RPT 2027 21-PDF staging merekod `teacher_text_leak_report.json` di artifak (audit sahaja). Mod `--fail-on-findings` ialah pagar wajib apabila hendak mengeluarkan PDF teacher-ready.

## Prinsip pembetulan
1. **Asingkan** metadata audit/draf/approval daripada jadual guru. Jangan buang nota daripada log sumber atau bukti signoff.
2. **Hapus daripada paparan guru** frasa arahan pembangun, status checkpoint, komen pembetulan dan nota verifikasi dalaman.
3. Jika maklumat SK/SP/rujukan BT/BA belum sah, **tahan penerbitan PdP atau dokumen itu**, bukan menggantikan dengan nombor atau pernyataan rekaan.
4. Bahan staging kekal bertanda draf secara jelas di ruang semakan admin; jangan menipu dengan menukarnya menjadi FINAL.
5. Sebelum aktif di Telegram/Web: PDF per halaman mesti lulus audit kebocoran **dan** signoff akademik, kalendar A/B, padanan RPH/buku teks, serta E2E muat turun. Sains legacy dan enam rekod PI tertahan di PR #441 kekal release-blocking.
6. Tiada DB, `main`, Web/Telegram live atau fail asal diubah oleh audit ini.

## Cara mengaudit secara manual
```bash
python -m scripts.audit_rpt2027_teacher_text_leaks_20261108 --teacher-output-only --output /tmp/rpt_teacher_leak_report.json rpt_2027 staging/rpt_2027_seragam_2026/pdf
# Selepas dokumen benar-benar lulus signoff:
python -m scripts.audit_rpt2027_teacher_text_leaks_20261108 --teacher-output-only --fail-on-findings /path/to/final_rpt_pdf
```

## Peluasan QA semua 56 PDF (8 Nov, menunggu CI)
Pengesan kini disepadukan **secara baca sahaja** ke dalam lima workflow yang membina:
- 21 PDF utama (PSV, Moral, RBT, Sejarah, PJPK)
- 20 PDF BM, Pendidikan Islam, Bahasa Arab dan Muzik
- 5 PDF Matematik
- 5 PDF English
- 5 PDF Sains separa/legacy (tetap tidak layak keluaran)

Jumlah sasaran: **56 PDF**, setiap aliran memuat naik JSON audit sebagai artifak bersama PDF. Ini adalah skop *ujian yang dikonfigurasikan*, bukan dakwaan keputusan lulus — hasil CI dan bilangan frasa sebenar perlu dibaca daripada laporan setelah workflow siap. Audit frasa ini tidak menggantikan pengesahan akademik, rekod Jawi/Arab, edisi DSKP, atau ujian Telegram/Web LIVE.
