# PSV Tahun 6 — audit semantik Unit 1–3 dan SP Projek Seni Visual
**Tarikh:** 4 November 2026
**Branch:** `psv-y2-y6-rpt-rph-2027-staging-20261104` (PR #196, staging)
**Status:** DRAF SEMAK — bukan FINAL READY / bukan Telegram LIVE

## Rujukan diperiksa
- DSKP KSSR PSV Tahun 6 terbitan BPK/KPM 2021, **halaman bercetak 32**, bahagian Projek Seni Visual: https://asiemodel.net/wp-content/uploads/2022/08/8.-DSKP-KSSR-SEMAKAN-2017-PENDIDIKAN-SENI-VISUAL-TAHUN-6_ISBN_.pdf
- Buku Teks Pendidikan Seni Visual Tahun 6, **halaman bercetak 10–25**, Unit 1–3: https://fliphtml5.com/hkvtu/cnbo/Pendidikan_Seni_Visual_Tahun_6/
- RPT PSV Tahun 6 2026 sebagai semakan urutan: https://anyflip.com/zxzlm/tuth/basic

## Pembetulan sumber yang disahkan
**1. Modul Projek Seni Visual**
- SP 5.1.4: mengurus karya dan alatan supaya selamat **semasa** pameran.
- SP 5.1.5: menyusun alatan dan membersihkan ruang **selepas** pameran.
- RPH **PdP 026 dan 042** menggunakan 5.1.4 untuk tindakan selepas pameran dan mengandungi catatan salah bahawa 5.1.5 bukan kod Tahun 6. Kedua-duanya telah dibetulkan kepada **5.1.5**; baris RPT CSV Tahun 6 turut diselaraskan. HTML RPT sebelum ini sudah menggunakan 5.1.5 dan dikekalkan.

**2. Buku teks Tahun 6 Unit 1–3**
| PdP | Aktiviti | Halaman BT bercetak | Pembetulan kandungan utama |
|---|---|---|---|
| 002 | Alat Tulis Saya | 10–11 | Lakaran peniruan alat tulis, garisan selari/silang pangkah/kontur, perbandingan dua media; membuang aktiviti pemandangan kampung yang tersalah |
| 003 | Tingkap Damai | 12–13 | Tetingkap fokus dan lakaran pemandangan dengan ruang hadapan/tengah/belakang serta kesan perspektif |
| 004 | Dunia Gemilang | 14–15 | Analisis arca 3D, imbangan tidak simetri, bentuk dan kontra warna; bukan model kotak |
| 005 | Bersatu Teguh Bercerai Roboh | 16–17 | Arca stabail menggunakan cantuman tanggam prapotong, ujian tapak dan imbangan; bukan kotak kejutan |
| 006 | Kotak Kejutan | 18–19 | Bentangan kotak, lipatan, pembinaan model dengan sambungan dan ujian kekukuhan |
| 007 | Realiti Alam | 20–21 | Analisis ruang ilusi, penegasan dan kepelbagaian pada imej alam; bukan tugasan kaktus |
| 008 | Lihat dan Sentuh | 22–23 | Capan dan kolaj untuk jalinan tampak/sentuh; bukan tugasan kaktus |
| 009 | Kaktus Khatulistiwa | 24–25 | Lipat/gunting kertas warna dan montaj kaktus di atas imej pasu, jalinan serta harmoni |

Bagi **PdP 002–009**, RPH dan RPT CSV telah dipadankan dari segi objektif, kriteria kejayaan/evidens PBD, tajuk dan rujukan halaman. RPT HTML (landskap) menyatakan halaman khusus yang sama. Kod SK/SP untuk PdP 002–009 tidak ditukar kerana pembetulan yang dikenal pasti ialah aktiviti/hasil, bukan kod. Status kekal `DRAF_SEMAK`.

## Kawalan perubahan dan pengujian
- Fail diubah hanya dalam branch staging PR #196; tiada sentuhan pada `main`, DB pengguna, Telegram atau produksi.
- Semua versi sebelum pembetulan kekal dalam sejarah commit branch; backup asal projek sedia ada tidak dipadam.
- Ujian regresi `tests/test_psv_rpt_rph_source_order.py` ditambah untuk memeriksa PdP 002–009 dan 026/042.
- **Semakan terarah melalui bacaan semula GitHub**: 10 RPH + 1 RPT CSV + 1 RPT HTML, keseluruhan **12 fail**, lulus padanan objektif, PBD, halaman BT dan SP Projek bagi skop di atas. Ini **bukan** larian Python `unittest` atau GitHub Actions.

## Belum disahkan
- Semakan visual semua halaman 50 unit dan audit semantik menyeluruh 210 RPH.
- Keperluan 1 halaman A4 Word/PDF RPH, RPT PDF lanskap serta urutan hari sekolah/cuti Kumpulan A/B 2027.
- CI lulus, integrasi bot, DB staging, dan penggunaan sebenar guru.

**Keputusan:** 10 RPH Tahun 6 mendapat pembetulan khusus dan lulus semakan konsistensi terarah, tetapi keseluruhan PSV Tahun 2–6 belum boleh ditandakan FINAL READY atau digabungkan ke `main`.
