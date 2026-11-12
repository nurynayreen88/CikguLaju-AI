# English Tahun 4 — audit pemetaan halaman Student Book (11 November 2026)

## Skop dan sumber
- Baca kod sumber `app.py` pada cabang PR #558: `_Y4_SB_PAGES_V25230`, `_EN34_MAIN_SB_V25231`, `_EN_LOCAL_BOOK_CHUNKS_V25234`.
- Terdapat **81 Lesson** dengan rekod muka surat pada peta terverifikasi kod Telegram. Ini bukan dakwaan semua 160 Lesson telah disemak secara visual.
- Daripada 81: **80 Lesson** memenuhi pengadang asal 1–4 halaman utama berturutan. **Lesson 43** ialah rujukan lama yang salah, kini diperbetulkan khusus kepada Student Book **halaman 121** mengikut *Primary Year 4 SK Scheme of Work*, Lesson 43 (Phonics 3). Keseluruhan **81/81** laluan sumber API boleh diuji dalam staging, tertakluk hak edaran dan pengesahan visual.
- **14 Lesson** mempunyai lebih daripada satu halaman, termasuk Lesson 18 (`15, 16`) dan Lesson 103 (`73, 74–75`).
- **Lesson 43**: peta Telegram lama memetakan **5 halaman salah** (`27, 28, 29, 30, 31`). Rujukan *Primary Year 4 SK Scheme of Work* (Lesson 43, Phonics 3) menyatakan **Student Book p.121**. Resolver API staging hanya membetulkan rekod spesifik apabila padanan lama itu tepat, tanpa mengubah had empat halaman untuk Lesson lain. Peta lama dalam `app.py` masih memerlukan pembetulan berasingan bagi laluan Telegram legasi.
- **Lesson 157**: peta lama `110–133` telah digantikan untuk **halaman utama 110**; halaman 133 direkod sebagai bahan tambahan berasingan. Jangan dedahkan 110–133 sebagai satu muat turun.

## Penemuan ketepatan parser
- Pembaca Telegram lama `_v25232_nums` hanya mengekstrak satu nombor/rentang awal; contohnya `15, 16` menjadi `[15]` dan `73, 74–75` menjadi `[73]`.
- Resolver endpoint Student Book Year 4 baharu kini membaca **semua** token senarai/rentang yang disahkan, dengan pemeriksaan berturutan, tiada duplikasi, dan maksimum empat halaman. Pengecualian peta sumber Lesson 43 dilakukan pada resolusi metadata **sebelum** parsing umum, dan hanya mengeluarkan satu halaman p.121.
- Ujian baharu mengawal parser dan pemeriksaan kandungan fail PDF sumber sebenar tiga bahagian: `y4_student_001_020.pdf`, `y4_student_021_100.pdf`, `y4_student_101_177.pdf`.
- Tiada perubahan kepada parser/DB/RPH/kredit/Telegram menu lama.

## Had pengesahan / release gate
- Lulus CI PDF dan sumber ialah pemeriksaan struktur sahaja; **belum membuktikan** setiap halaman PDF secara visual sepadan dengan muka surat cetak sebenar.
- Ujian aliran Web–Telegram dengan akaun guru dan deployment sebenar belum disahkan. **DRAFT / STAGING HOLD; jangan gabung/deploy sebelum QA tersebut.**
- Semua bahan kurang yakin kekal tidak tersedia; jangan meneka halaman atau memindahkan status akademik kepada READY.

## Pembetulan khusus Lesson 43 — 12 November 2026

- Rujukan utama: *Primary Year 4 SK Scheme of Work*, Lesson 43, Phonics 3, **Get Smart Plus 4 Student’s Book p.121**, halaman paparan sumber 133: https://online.anyflip.com/aecw/prtt/files/basic-html/page133.html .
- Rujukan silang RPT 2026 yang sama: https://www.scribd.com/document/990880280/Rpt-English-Year-4-Sk-2026 . Halaman 27–31 menerangkan aktiviti Unit 3 lain, bukan bahan Phonics 3 Lesson 43.
- Ujian baharu mengekstrak tepat satu halaman daripada sumber `y4_student_101_177.pdf`, membandingkan data halaman asal; bukan melonggarkan penghad empat halaman untuk Lesson lain.
- **Status: STAGING, BELUM LIVE.** Pemulihan halaman rujukan tidak membuktikan hak edaran, ketepatan visual keseluruhan buku, atau ujian HTTPS Web–Telegram; bahan tidak dipromosikan sebagai FINAL READY.
