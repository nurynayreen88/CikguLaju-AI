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

## Hasil sebenar GitHub Actions, 8 November 2026 (staging)
Lima aliran penjanaan PDF telah berjaya menjalankan audit bacaan halaman dengan **0 read_errors** selepas pembaikan PyMuPDF (semua ini ialah PDF **pratayang**, bukan muat turun LIVE yang disahkan):
| Binaan | PDF / fail diperiksa | Fail ada frasa dalaman | Padanan frasa |
| --- | ---: | ---: | ---: |
| English Tahun 2–6 | 5 | 5 | 202 |
| Matematik Tahun 2–6 | 5 | 5 | 252 |
| BM, PI, Bahasa Arab, Muzik | 20 | 20 | 1,389 |
| Sains Tahun 2–6 (sumber legacy separa) | 5 | 5 | 94 |
| PSV/Moral/RBT/Sejarah/PJPK + PDF sedia ada di `rpt_2027` | **64** | **39** | 642 |

**Penting:** Pada kelompok terakhir, 64 fail itu ialah gabungan **21 PDF pratayang** dan **43 PDF sedia ada**, bukan 64 RPT baharu. Setelah masalah denominator ditemui, workflow diubah untuk mengeluarkan laporan **berasingan** bagi 21 dan 43 PDF. Jangan dedahkan "39 daripada 21" atau gabungkan counts seolah-olah 56 PDF utama sahaja.

**Kesilapan QA yang sudah dibaiki:** audit Sains pertama melaporkan 0 padanan kerana `pypdf` tidak terpasang (lima `read_errors`), sementara workflow tetap `success`. Kini scanner mengutamakan `fitz`, menggunakan `pypdf` sebagai fallback, dan return kod gagal jika mana-mana fail tidak boleh dibaca atau folder kosong. Ulangan menghasilkan **94 padanan, 5/5 PDF, read_errors=[]**. Empat ujian scanner awal lulus; ujian lanjutan fail rosak/folder kosong telah ditambah dan tertakluk pengesahan CI komit paling baharu.

Penanda `DRAF SEMAKAN` yang berulang pada footer bukan isi akademik tetapi tetap kebocoran metadata pembangun ke salinan guru. *Bilangan padanan* bukan bilangan PdP kurikulum salah atau jumlah penggantian frasa yang selamat secara automatik.

**Keputusan release: HOLD.** Belum ada PDF guru baharu yang diterbitkan; pemeriksaan ini mengenal pasti masalah dan menyediakan guardrail audit, bukan menyembunyikan jurang SK/SP/DSKP yang belum siap.

## Keputusan akhir audit bacaan PDF pratayang (8 Nov 2026)
Selepas pemisahan laporan, QA 21 PDF utama mengeluarkan **21 fail, 21 terkesan, 503 padanan, 0 ralat bacaan**. QA PDF sedia ada `rpt_2027` mengeluarkan **43 fail, 18 terkesan, 139 padanan, 0 ralat bacaan**. Digabung dengan empat kelompok pratayang lain:

| Kelompok 56 PDF staging | PDF diperiksa | Fail terkesan | Padanan |
| --- | ---: | ---: | ---: |
| PSV / Moral / RBT / Sejarah / PJPK | 21 | 21 | 503 |
| BM / Pendidikan Islam / Bahasa Arab / Muzik | 20 | 20 | 1,389 |
| Matematik | 5 | 5 | 252 |
| English | 5 | 5 | 202 |
| Sains | 5 | 5 | 94 |
| **JUMLAH PRATAYANG** | **56** | **56** | **2,440** |
| PDF lama sedia ada (auditan berasingan) | 43 | 18 | 139 |

**Semua kelompok PDF yang ditunjukkan di atas mempunyai 0 `read_errors` dalam run QA yang selesai.** Ujian keselamatan bagi fail rosak/folder kosong dan scanner fail-closed telah ditambah dalam staging. **PDF bersih guru belum dikeluarkan; signoff akademik masih wajib.**

Kepentingan pengesanan: banyak padanan `DRAF SEMAKAN` berasal dari header/footer berulang, dan bahan Bahasa Arab masih memaparkan `belum dipadankan` kerana standard Arab belum disahkan. Frasa itu perlu diletakkan di metadata semakan admin, tetapi ia tidak boleh dipadam daripada dokumen untuk guru sehingga bahan yang terjejas benar-benar disahkan/diganti dengan kandungan tepat.

## Pembetulan paparan guru dan kawalan penerbitan (8 Nov 2026)
- `rpt_2027/common/teacher_display_projection.py` memisahkan catatan guru daripada metadata pembangun semasa render sahaja; rekod sumber, SK/SP rasmi, checksum dan ledger HOLD **tidak diubah**.
- `rpt_2027/common/format_2026_layout_preview.py` kini tidak lagi memaparkan footer `DRAF SEMAKAN`, arahan sumber audit atau placeholder minggu `Belum ditentukan` dalam PDF pratayang. Nilai minggu sebenar dalam sumber tetap tidak direka.
- Pemeriksaan PDF sebenar selepas pembetulan awal: 21 PDF PSV/Moral/RBT/Sejarah/PJPK = **0 padanan**, 20 PDF BM/PI/Arab/Muzik = **0 padanan**, 5 Matematik = **0**, 5 English = **0**, 5 Sains = **0**, semua tanpa ralat baca. Jumlah awal **56/56** lulus frasa pemeriksa tahap pertama.
- Semakan visual berjaya mengesan **kelas kes tambahan yang pengesan awal terlepas**: pada PDF PJPK, catatan `Sumber: PJ456_2027_RPT` dan `Rujukan: Rujuk DSKP` berulang. Pemeriksaan bebas atas artifak pertama mengira 339 label `Sumber:` dan 163 `Rujukan: Rujuk DSKP` pada lima PDF PJPK. Pengguguran provenance ini kini dibuat pada lapisan paparan; butiran buku teks/PBD dikekalkan.
- Pengesan ditambah untuk `INTERNAL_SOURCE_ID`, `UNHELPFUL_REFERENCE_DIRECTIVE` dan `HELD_REVIEW_ONLY`. Lima workflow binaan PDF menggunakan `--fail-on-findings` supaya output yang masih membawa bahasa pembangun **gagal QA**; PDF lama masih dilaporkan berasingan.
- QA ujian pengekalan semantik meliputi SK/SP rasmi `Menulis draf` (mesti dikekalkan) supaya perkataan akademik `draf` **tidak** disalah baca sebagai status pembangun. Juga merangkumi BM Tahun 2 PdP 130/131 HOLD dan catatan PBD/aktiviti PJPK.
- **Perhatian status:** ujian CI terakhir bagi pengesan diperluas dan pemeliharaan PBD sedang menunggu giliran Actions; **jangan klaim tahap kedua lulus 56/56** sebelum hasil akhir dibaca.

## Masih tertahan (jangan samakan pembetulan ayat dengan kebenaran release)
- **18 daripada 43 PDF sedia ada** masih membawa nota dalaman; belum di-overwrite atau diubah pada produksi.
- Bahasa Arab: SK/SP penuh rasmi belum ditandatangani walaupun kod dan halaman DSKP diindeks.
- Sains: konflik edisi DSKP/legacy dan padanan PdP–RPH masih kritikal.
- Pendidikan Islam: enam sumber RPH/PdP tertahan, termasuk isu Tahun 6.
- RBT: jadual minggu sebenar tidak boleh diisi secara tekaan.
- Pengesahan kalendar, rujukan buku, keseragaman Word/PDF, dan muat turun Web/Telegram E2E masih prasyarat sebelum FULL READY.

**Release gate:** PASS pemeriksaan teks sahaja != PASS akademik. PR kekal draft, tidak di-merge ke `main` atau di-deploy.
