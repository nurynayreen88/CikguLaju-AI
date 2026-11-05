# CikguLaju · Sejarah Tahun 4–6 · RPT & RPH 2027

**STATUS: DRAF KANDUNGAN / STAGING. BUKAN FINAL READY.** Bahan ini tidak mengubah `main`, `app.py`, DB, Telegram, Web, pengguna, pembayaran atau menu.

## Hasil
- 3 pemetaan DSKP rasmi, 33 SK dan 228 SP (termasuk kod K kewarganegaraan/sivik) yang diekstrak daripada PDF DSKP pengguna dalam Google Drive.
- 3 RPT CSV 2027, 3 RPT HTML bercetak **landscape**, 36 PdP setahun = 108 PdP.
- 108 RPH Markdown individu dan 3 HTML himpunan RPH untuk cetak **A4 portrait** (5+20+20+10+5 minit).
- Setiap tahun: 32 PdP kandungan + 4 PdP kajian kes **susunan cadangan**, tidak dianggap bilangan PdP rasmi KPM.
- Kumpulan A/B memaparkan julat minggu cadangan daripada kalendar akademik 2027. **Jangan** anggap ia tarikh kelas yang disahkan; cuti negeri dan jadual waktu guru mesti ditentukan kemudian.
- Logo dan maklumat sekolah ialah ruang template untuk profil pengguna, bukan data sebenar yang telah disuntik.
- Tiada halaman buku teks direka atau dituntut disahkan. Buku Teks Sejarah Tahun 4 sumber PDF telah dikenal pasti; untuk Tahun 5–6 perlu semak buku edisi dan halaman aktiviti sebenar.

## Sumber
- DSKP KSSR Sejarah Tahun 4: https://drive.google.com/file/d/1lKTJr3UpUn-miV_FUwIu46kV4KWZr4zP/view
- DSKP KSSR Sejarah Tahun 5: https://drive.google.com/file/d/1eOv2FMk3LWsb6O7W4bsQFjVUylQDsGri/view
- DSKP KSSR Sejarah Tahun 6: https://drive.google.com/file/d/1BN6nJjse61rXyaA9YKTsiIJm7ylmQc4Q/view
- Kalendar Akademik KPM 2027: https://www.moe.gov.my/index.php/kalendar-akademik-semasa

## Pintu semakan sebelum pengaktifan
1. Pengesahan silang **setiap** kod SK/SP terhadap dokumen DSKP dan setiap RPH untuk kandungan sejarah, inferens dan KPS.
2. Padankan setiap PdP dengan halaman **buku teks edisi sebenar** Tahun 4–6 dan semak arahan guru/murid; elakkan fakta sejarah tanpa sumber.
3. Sahkan kaedah pelaksanaan Kajian Kes, jadual 2027 Kumpulan A/B, cuti umum/gantian negeri dan jumlah masa Sejarah sekolah.
4. Uji cetakan HTML menjadi Word/PDF satu muka A4 RPH, RPT landscape dengan muka depan dan logo profil, kemudian semak imej/teks.
5. Integrasi penjana runtime **yang sama** untuk Telegram dan Web, uji guru sebenar di staging sebelum deploy. Tiada pelaksanaan ini dibuat dalam perubahan ini.
6. Kekalkan keputusan kelulusan manusia per PdP; hanya naikkan status apabila bukti lengkap.

Jalankan: `python scripts/check_sejarah_y4_y6_2027.py`.

Nota: RPH ialah draf khusus topik dan SP, bukan pengesahan pedagogi seorang demi seorang.

## Kemajuan teknikal terkini (6 November 2026)

- **108/108 RPH** dan **36 PdP/Tahun** lengkap sebagai bahan draf unit/SP, 33 SK dan 228 SP; RPT 2027 Kumpulan A/B disemak minggu cuti penggal/perayaan.
- **Word preview** telah dijana dan diuji di GitHub Actions; 108 RPH sebenar dalam Word dibaca semula selepas penukaran PDF, **satu A4 setiap PdP**. 3 RPT landscape Word/PDF, 5 halaman setahun. Pembetulan font, lebar dan jadual RPT telah diuji; sampel visual diperiksa.
- **PDF preview** daripada HTML turut lulus. Tiga workflow Sejarah terbaru lulus pada commit `bd170c29bda6217220b9379e229eb435237accc6`.
- **Fail-closed source contract:** `web/sejarah_2027_staging_source.py` dan `scripts/check_sejarah_release_gates_2027.py` memastikan 108/108 RPH DRAF tidak boleh dibuka sebagai eksport pengguna.
- Status individu 108 RPH dan pagar kelulusan: `audits/sejarah_y4_y6_release_approval_manifest_20261106.json` dan `.md`.
- **Belum FINAL READY:** halaman aktiviti sebenar BT setiap PdP, kelulusan pedagogi individu, suntikan logo sekolah sebenar, kalendar negeri/jadual guru dan ujian enjin natif Telegram–Web belum disahkan. Word/PDF yang berjaya diuji ialah **penjana pratonton berasingan**, bukan pengesahan runtime produksi.

Semua kerja masih pada PR #341 DRAF. Jangan gabung atau deploy atas keputusan QA teknikal sahaja.

## Penambahan semakan sumber dan keselamatan (6 November 2026)

- **11/108 RPH** kini ada rujukan halaman buku teks khusus yang disemak melalui teks digital (Tahun 5 PdP 005–009, Tahun 6 PdP 001–006). Lihat `audits/sejarah_y4_y6_primary_textbook_page_evidence_20261106.json`. Ini belum sama dengan kelulusan visual tugasan atau guru.
- **Pagar kelulusan bebas** menghendaki rekod `audits/sejarah_y4_y6_release_approval_manifest_20261106.json` dan fingerprint sumber sepadan sebelum data boleh diserahkan untuk eksport natif. Meminda status sumber semata-mata tidak mengaktifkan akses.
- Semua dokumen masih DRAF. Jangan merge ke main atau deploy sehingga tanda tangan pengesahan setiap PdP serta QA Telegram–Web betul-betul lengkap.

- **Kemajuan bukti teks halaman terkini: 18/108 PdP** (Tahun 4 PdP 001–007, Tahun 5 PdP 005–009, Tahun 6 PdP 001–006). Rekod terdahulu menyebut 11/108; rujuk ledger JSON untuk bilangan terkini. Semua kelulusan kekal belum lengkap.

- **Semakan halaman teks terkini**: Tahun 4 36/36, keseluruhan 47/108. Semua status DRAF dan kelulusan individu belum disahkan. Rujuk ledger bukti untuk nilai terkini.

- Tambahan bacaan teks Sejarah Tahun 6 PdP 007–014. Semakan halaman khusus keseluruhan **55/108**, tanpa kelulusan latihan atau guru. Semua DRAF.
