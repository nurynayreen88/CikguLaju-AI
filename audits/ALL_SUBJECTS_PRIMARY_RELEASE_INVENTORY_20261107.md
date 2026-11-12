# Status keseluruhan subjek CikguLaju — inventori audit 7 November 2026

**Kesimpulan: TIDAK SEMUA SUBJEK SIAP / FINAL READY.** 
**Skop:** Sekolah rendah, kandungan Tahun 2–6. Audit berasaskan fail yang tersedia dalam repositori pada 7 Nov 2026; **bukan** pengujian pengguna hujung-ke-hujung terhadap Web dan Telegram yang aktif. Tahun 1 KP2027 dan semua subjek menengah memerlukan inventori berasingan.

## Takrif status yang tidak boleh dicampur

- **Bahan ada:** sumber atau PDF/RPH wujud dalam repo/staging.
- **Audit struktur lulus:** bilangan PdP, fail, kod, susun atur dan penjanaan telah diuji.
- **Audit kurikulum lulus:** SK/SP, susunan, aktiviti sebenar, bahasa, buku teks dan PBD disemak terhadap sumber; dakwaan kelulusan bagi semua PdP mestilah benar dan dapat diulang.
- **Boleh guna LIVE:** kandungan terkini diuji dalam Web dan Telegram sebenar daripada **sumber DB sama**, termasuk Word/PDF, muat turun bahan, hak akses/kuota dan perubahan data tanpa overwrite.

Lulus satu peringkat **tidak** menaikkan semua peringkat lain. Pengguna tidak perlu membuat audit saya: tanggungjawab audit kandungan ialah pada penyediaan CikguLaju. Untuk operasi kelas sebenar, pentadbir sekolah/guru tetap menentukan jadual dan keselamatan amali mengikut tempat.

## Matriks semakan sekolah rendah Tahun 2–6

| Subjek | Bukti kerja yang telah tersedia | Penilaian status semasa | Kerja yang belum lulus |
|---|---|---|---|
| English | **800/800** RPH/RPT Lesson T2–6, QA teknikal pemetaan SOW/Word/PDF | **Banyak tersedia; belum FINAL READY keseluruhan** | 33 lesson pilihan guru; audio konflik Y4 L30 dan pautan buku salah Y4; ketepatan SB/WB/audio penuh; RPT jadual A/B dan ujian live |
| Bahasa Melayu | **5 PDF RPT 2027** T2–6, **164–166 PdP** setahun, status `DRAF_BELUM_READY` | **DRAF** | Mutu RPH tidak generik; semakan SK/SP dan buku teks/aktiviti; keseragaman RPT serta ujian live |
| Matematik | **5 PDF RPT T2–6** v28 `SEMENTARA`, Lesson 001–117 | **SEMENTARA** | Aktiviti RPH khusus, padanan buku latihan/halaman setiap lesson, SK/SP, perbandingan RPT dan Web |
| Sains | Sumber pelbagai versi/DB lama; fail `rpt_2027/sains/tahun3_unit_order_source_candidate_20261106.json` cuma susunan 10 unit | **RPT 2027 lengkap tidak dapat disahkan** | Urutan PdP sebenar T2–6, eksperimen/kemahiran sains, DSKP dan buku teks/aktiviti, RPT A/B dan generator live |
| Pendidikan Islam | **690 RPH draf boleh dibaca**, 6 rekod dipegang daripada asal 696; 5 PDF RPT T2–6 | **DRAF; bukan FINAL READY** | Pembetulan 6 held, semak SK/SP/Jawi/Quran/halaman, mutu aktiviti dan native runtime |
| Pendidikan Moral | **210 RPH T2–6**, 70 unit, 350 SP, draf RPT tambahan | **DRAF; DB parity pernah gagal** | SP T2 4.4 dalam DB v26.00 salah; audit buku per PdP, masa PdP mingguan, source parity/live |
| PJPK | **400 PdP/komponen PJ/PK calon T2–6** berdasarkan 10 kiraan `41+53+38+41+34+41+33+44+34+41`; 5 PDF RPT DRAF | **DRAF** | Semak instrumen/aktiviti PJ/PK, keselamatan akuatik, rujukan buku, cuti negeri dan PDF/live |
| PSV | **210 RPH T2–6**, **42 setiap tahun**, RPT/PDF; audit Word A4 teknikal lulus | **DRAF; 0/210 kelulusan isi pada manifest terdahulu** | Audit buku/aktiviti/karya/PBD bagi PdP dan laluan runtime |
| RBT | **96 RPH T4–6**, 32 setahun; 16 SK, 114 SP diperiksa; 21 PDF gabungan termasuk 3 RBT; 3 simulasi minggu berasingan | **DRAF** | RPT jadual sebenar 96 PdP, aktiviti keselamatan, pengesahan visual Tahun 5–6, Web/Telegram |
| Sejarah | **108 RPH T4–6**, 36 setahun; PDF RPT/Word serta halaman buku khusus dalam pratonton | **DRAF** | Audit aktiviti sumber buku dan PBD individu, latihan/teks/imej serta native/live |
| Bahasa Arab | **298 RPH DRAF T2–6**, 20 indeks unit, Word/PDF A4 teknikal | **DRAF_STAGING_RELEASE_BLOCKED** | RPT A/B lengkap, buku cetakan sepadan, Jawi/Arab/SP/linguistik/aktiviti, native/live |
| Pendidikan Muzik | **175 RPH + 5 RPT T2–6**, 35 setiap tahun, staging | **DRAF** | Konflik SP T4 dan edisi buku salah, rujukan audio, aktiviti buku, integrasi native MUZIK belum wujud |

Kiraan PJPK pada versi sumber tergolong dalam **PdP calon mengikut komponen PJ/PK**, bukan pengesahan keunikan PdP keseluruhan atau susunan minggu. Kiraan bahan di atas ialah **inventori fail/release manifest**, bukannya peratus kesiapsiagaan rasmi.

## Isu silang-subjek yang mesti ditutup sebelum semua boleh guna

1. **Kurikulum:** padanan SP pernyataan penuh, SK, urutan PdP, tahun, tema/unit, buku teks dan buku aktiviti; status konflik sumber mesti diselesaikan (jangan auto reka standard).
2. **Kandungan:** langkah aktiviti guru/murid mesti khusus subjek, bukan teks templat; satu halaman A4 Word/PDF yang benar-benar boleh digunakan; PBD, BBM, keselamatan amali/PE/muzik mengikut subjek.
3. **RPT:** semua subjek menggunakan **lima lajur seragam** `MINGGU/TARIKH | UNIT/TAJUK/PDP | SK | SP | CATATAN`; minggu gabung menegak apabila sama, SP/SK pernyataan penuh. Muka depan logo, nama sekolah dan nama guru sahaja selain tajuk/subjek/tahun.
4. **Kalendar 2027:** tarikh kumpulan A/B dan cuti negeri + gantian, bukan turunan 2026; jadual kelas sebenar tidak boleh direka.
5. **Penerbitan:** satu DB/sumber canonical Telegram dan Web; periksa paparan, butang muat turun, janaan Word/PDF, status pengguna, akses RPT dan kuota; staging sebelum produksi.
6. **Tahun 1 KP2027:** bahan T1 lama tidak boleh disebut KP2027 FINAL tanpa dokumen/kurikulum sah 2027; mesti peringkat berasingan.
7. **Sekolah menengah:** belum ada audit menyeluruh disahkan dalam matriks ini. Jangan simpulkan semua Tingkatan 1–5 siap daripada pencapaian sekolah rendah.

## Cara audit berikutnya — tanggungjawab penyedia kandungan, bukan pengguna

- Gunakan sumber DSKP/KPM/SOW dan buku teks yang memang ada; tambah pencarian sumber apabila bahan tiada. Audit kurikulum per PdP/lesson boleh diselesaikan oleh penyedia tanpa meminta pengguna menyemak setiap item.
- Utamakan **Sains, Bahasa Melayu, Matematik, Pendidikan Islam, Muzik, Bahasa Arab** kerana bukti RPT/aktiviti paling banyak jurang, kemudian **Moral, PJPK, PSV, RBT, Sejarah, English** bagi konflik tersisa. Susunan boleh berubah jika audit live menunjukkan kegagalan yang lebih berat.
- Hasil akhir bukan jumlah PDF, tetapi matriks subjek × tahun × PdP yang menyimpan `curriculum_match`, `textbook_match`, `activity_quality`, `word_pdf`, `calendar`, `web_telegram_parity`, `ready` dan isu konkrit. Jangan memberikan skor/peratus tidak bersumber.
- Label **FINAL READY** hanya selepas ujian berulang dan bukti fail/runtime lengkap. Tiada reset DB, tiada overwrite dan jangan automatik merge PR #441; audit di staging ini tidak meluluskan produksi.

## Sumber yang dilihat untuk matriks

- `rpt_2027/english/README.md` + `audits/english_2_6_800_lesson_technical_readiness_20261104.md`
- `rpt_2027/bahasa_melayu/PDF_DRAF_MANIFEST_2027.json`
- `rpt_2027/matematik/README.md`, `rpt_2027/sains/tahun3_unit_order_source_candidate_20261106.json`
- `rph_standalone/pendidikan_islam_draf_2027/README.md`
- `audits/pm_y2_y6_release_gate_20261104.md`
- `audits/pjpk_2027_staging_manifest_20261104.json`
- `audits/psv_ready_gate_status_20261105.md`
- `rpt_2027/rbt/README.md`, `audits/rbt_y5_y6_64_pdp_book_mapping_and_sample_source_review_20261107.md`
- `audits/sejarah_y4_y6_release_approval_manifest_20261106.json`
- `audits/bahasa_arab_release_readiness_20261106.json`
- `staging/pendidikan_muzik/rpt_rph_2027/QUALITY_GATE_20261105.md` dan `INTEGRATION_WORD_PDF_RELEASE_GATE_20261106.md`

**Keputusan 7 Nov 2026:** Tiada asas untuk mengumumkan semua subjek **FINAL READY**. Sistem ada bahan yang banyak, tetapi status subjek penuh belum lulus audit kurikulum dan produksi.
