# English Tahun 4 Student Book — pemurnian Telegram legasi (12 November 2026)

**Status:** STAGING / PRE-RELEASE HOLD. Bukan pengesahan semua 160 Lesson atau muat turun LIVE.

## Punca disahkan di `app.py`

- Peta `_Y4_SB_PAGES_V25230` mempunyai **81** Lesson dengan rujukan Student Book.
- Parser lama `_v25232_nums` mengambil nombor/julat **pertama sahaja** selepas `m/s`; contohnya `15, 16` menghantar halaman **15** sahaja, lalu membuang halaman 16.
- Resolver Y4 yang tidak berjaya dahulu boleh menggunakan nombor halaman lama dalam keadaan sesi. Pemurnian ini menolak fallback sebegitu apabila rekod Lesson Tahun 4 tidak lengkap.

## Pemetaan sumber yang dibetulkan

| Lesson | Peta lama | Rujukan Scheme of Work (SK) | Peta baharu |
|---|---|---|---|
| **43**, Listening 9 / Phonics 3 | 27, 28, 29, 30, 31 | Get Smart Plus 4, Phonics 3 Activities 1–2, Student Book p.121 | **121** |
| **103**, Speaking 20 / Helping out | 73, 74–75 | Get Smart Plus 4 Activity 5, Student Book p.73 | **73** |
| **157**, Reading 30 / What's the matter? | 110–133, dengan override 110 | *What are germs?* p.110; Activities 1–2 p.110–111. *Teeth facts!* p.133 ialah bacaan alternatif | **110–111** untuk pilihan utama; p.133 kekal berasingan |

**Sumber SOW:**
- Lesson 43: https://online.anyflip.com/aecw/prtt/files/basic-html/page134.html
- Lesson 103: https://anyflip.com/aecw/prtt/basic/251-300
- Lesson 157: https://anyflip.com/aecw/prtt/basic/351-398

## Keputusan pembaikan teknikal

1. Tiga rujukan di `app.py` dikemaskini. Override bahan utama Lesson 157 juga diselaraskan. Tiada SP atau susunan SOW lain direka.
2. Parser khusus Tahun 4 `_en4_verified_page_tokens_v20261112` memproses semua token senarai dan julat, maksimum **empat halaman berturutan** antara 1–177. Nombor berulang, julat terlalu panjang, halaman tidak berturutan dan teks tidak diketahui ditolak.
3. Pemilihan Student Book Tahun 4 tanpa rekod Lesson asal yang lengkap menghasilkan **tiada muat turun**, bukan rujukan cadangan atau halaman lama.
4. Tahun 3, Workbook Tahun 1–6, audio, RPH, pembayaran, identiti, kuota dan Supabase tidak disentuh.
5. Ujian AST memeriksa 81/81 peta struktur di `app.py` tanpa menjalankan bot. Ujian silang PR #558 memeriksa ekstrak PDF sumber asal. Ujian Web–Telegram PR #559 mempunyai pengadang muat turun yang berasingan.

**Penting:** 81/81 bermaksud pemetaan yang direkodkan disemak secara **struktur dan sumber PDF**; bukan 160/160 Lesson, bukan audit visual kandungan buku cetak atau kelulusan hak edar. Terdapat Lesson lain yang masih tiada pemetaan Student Book. Hak edaran, kelulusan akademik dan ujian HTTPS dengan akaun sebenar kekal prasyarat sebelum keluaran guru.

## Rujukan kerja berasingan

- PR #567: pembetulan peta lama `app.py` dan pengadang parser.
- PR #558: API Telegram Student Book/Workbook.
- PR #559: bahan Word/PDF Web, dengan ujian pasangan API Telegram.

Tiada auto-merge atau deployment untuk perubahan ini.
