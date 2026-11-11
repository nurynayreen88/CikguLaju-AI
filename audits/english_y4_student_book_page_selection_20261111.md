# English Tahun 4 — audit pemetaan halaman Student Book (11 November 2026)

## Skop dan sumber
- Baca kod sumber `app.py` pada cabang PR #558: `_Y4_SB_PAGES_V25230`, `_EN34_MAIN_SB_V25231`, `_EN_LOCAL_BOOK_CHUNKS_V25234`.
- Terdapat **81 Lesson** dengan rekod muka surat pada peta terverifikasi kod Telegram. Ini bukan dakwaan semua 160 Lesson telah disemak secara visual.
- Daripada 81: **80 Lesson** memenuhi pengadang 1–4 halaman utama berturutan (calon untuk muat turun); **1 Lesson** kekal HOLD.
- **14 Lesson** mempunyai lebih daripada satu halaman, termasuk Lesson 18 (`15, 16`) dan Lesson 103 (`73, 74–75`).
- **Lesson 43** memetakan **5 halaman** (`27, 28, 29, 30, 31`): dikecualikan daripada API baharu kerana had 4 halaman; perlu pengesahan guru/semakan had sebelum diterbitkan.
- **Lesson 157**: peta lama `110–133` telah digantikan untuk **halaman utama 110**; halaman 133 direkod sebagai bahan tambahan berasingan. Jangan dedahkan 110–133 sebagai satu muat turun.

## Penemuan ketepatan parser
- Pembaca Telegram lama `_v25232_nums` hanya mengekstrak satu nombor/rentang awal; contohnya `15, 16` menjadi `[15]` dan `73, 74–75` menjadi `[73]`.
- Resolver endpoint Student Book Year 4 baharu kini membaca **semua** token senarai/rentang yang disahkan, dengan pemeriksaan berturutan, tiada duplikasi, dan maksimum empat halaman.
- Ujian baharu mengawal parser dan pemeriksaan kandungan fail PDF sumber sebenar tiga bahagian: `y4_student_001_020.pdf`, `y4_student_021_100.pdf`, `y4_student_101_177.pdf`.
- Tiada perubahan kepada parser/DB/RPH/kredit/Telegram menu lama.

## Had pengesahan / release gate
- Lulus CI PDF dan sumber ialah pemeriksaan struktur sahaja; **belum membuktikan** setiap halaman PDF secara visual sepadan dengan muka surat cetak sebenar.
- Ujian aliran Web–Telegram dengan akaun guru dan deployment sebenar belum disahkan. **DRAFT / STAGING HOLD; jangan gabung/deploy sebelum QA tersebut.**
- Semua bahan kurang yakin kekal tidak tersedia; jangan meneka halaman atau memindahkan status akademik kepada READY.
