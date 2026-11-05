# PSV Tahun 2–6 — bukti QA terkini dan keputusan penerbitan

**5 November 2026 | PR #267 (STAGING) | commit asas 62657f7ab880fe5b655c2359e02484db7d97b757**

## Keputusan
- **QA TEKNIKAL: LULUS.** GitHub Actions https://github.com/nurynayreen88/CikguLaju-AI/actions/runs/41960157068 mengesahkan **53/53 ujian lulus** dan **210/210 RPH Word satu halaman A4**, tiada ralat. RPT/cover https://github.com/nurynayreen88/CikguLaju-AI/actions/runs/41960157069 juga lulus.
- **PENGESAHAN KANDUNGAN TERBIT: BELUM LULUS.** CSV `rph_standalone/psv/audits/psv_individual_210_review_20261105.csv` mempunyai **210 rekod** (42 setiap Tahun 2–6), **0 PASSED**, **0 rekod sijil visual buku `BUKU_TEKS_VISUAL_SAH:`**, dan **210 catatan semakan terbuka**.
- **PENERBITAN TELEGRAM LIVE: TIDAK DIAKTIFKAN.** PR #267 masih draft dan belum di-merge; `main` di hadapan staging sebanyak 13 commit pada audit perbandingan terkini; perubahan PSV tidak menyentuh database, bayaran, pengguna atau aktiviti subjek lain.
- **Ujian Telegram native staging:** Belum dibuktikan dengan service berasingan. Pratonton Web v1 di Render ialah service lain, bukan bot staging PSV.

## Apa yang sudah dimurnikan
1. Tahun 2 — **42/42 RPH disemak pada peringkat kandungan teks sumber** daripada Buku Teks asal; langkah produk daripada sayur/garisan selari hingga catan resis hidupan laut diperincikan. Proses projek Seni Visual (tanpa Seni Muzik) dan rujukan halaman RPT diselaraskan. Bukti: `audits/psv_y2_all_42_source_text_review_20261105.md`.
2. Tahun 3 — 42/42 RPH diperkemas dalam pusingan audit terdahulu, termasuk poster perayaan, capan kain, mobail serangga, model Parang Ilang hiasan, kolaj, gurisan, renjisan, boneka tali dan anyaman.
3. Tahun 4 — 42/42 RPH dibanding pada peringkat tajuk/unit/halaman, dengan 23 pembetulan isi khusus berasaskan PDF buku asal. Bukti: `audits/psv_y4_original_pdf_20261105.md`.
4. Tahun 5 — 42/42 RPH dimurnikan bersumberkan PDF asal. Bukti: `audits/psv_t5_original_pdf_20261105.md`.
5. Tahun 6 — 42/42 RPH diperiksa pada peringkat isi teks sumber, folio dan produk; rujukan asal projek dan fungsi arca koi berpusing diperbetul. Bukti: `audits/psv_y6_all_42_source_text_review_20261105.md`.
6. Peta induk `rpt_2027/psv/textbook_dskp_source_map_20261104.json` kini memuatkan **25 unit hasil karya yang dibetulkan**, tanpa mengubah kod SK/SP.

## Gerbang sebelum READY terbit
1. Semak secara visual **setiap** halaman Buku Teks bersesuaian bagi **210 PdP**; tandakan aktiviti guru/murid, bahan, keselamatan, PBD, SK/SP yang benar-benar telah disemak bersama bukti URL + nombor muka surat dalam CSV. Jangan mencipta rekod `PASSED` tanpa pemeriksaan sebenar.
2. Tutup 210 catatan semakan hanya selepas bukti bagi PdP tersebut lengkap dan semak RPT 2027 (kalendar Kumpulan A/B, cuti negeri/gantian).
3. Laksanakan Word+PDF melalui laluan native Telegram pada perkhidmatan staging PSV khusus, uji kelas/tarikh, aliran, kuota dan subjek lain.
4. Jalankan CI semula pada commit akhir, semak beza dengan `main` tanpa menimpa perubahan serentak dan hanya kemudian sediakan kelulusan sah di `rpt_2027/psv/psv_release_approval.json`.
5. Status produk **DRAF SEMAK** kekal sehingga empat gerbang di atas terbukti; jangan mengaktifkan ke LIVE secara paksa.

## Integriti
Fail `web/psv_2027_rph_release_bridge.py` menguatkuasakan ujian sumber, 210 rekod dengan sijil halaman, SHA-256 bagi dokumen, RPT/RPH READY, commit staging serta flag opt-in. Ketiadaan mana-mana syarat mesti menyebabkan adapter menolak penerbitan. Ini keputusan kejuruteraan yang disengajakan, bukan kegagalan menghasilkan 210 dokumen.
