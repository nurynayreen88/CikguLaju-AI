# Audit kesinambungan format RPH premium — subjek khas

Tarikh: 21 November 2026  
Piawaian wajib: [RPH Premium](RPH_PREMIUM_STANDARD_20261121.md)  
Penjejakan utama: [Isu #1182](https://github.com/nurynayreen88/CikguLaju-AI/issues/1182)

| Format / penjana | Keadaan sumber yang disemak | Ukuran / bentuk | Status bukti | Kerja lanjut |
|---|---|---|---|---|
| DLP Mathematics / Science (penjana `dlp_year2_rph.py`) | Kode Word/PDF menggunakan `_FIELD_WIDTHS=(48,134)`, `_ACTIVITY_WIDTHS=(32,122,28)`, panel tajuk `182 mm` | Semua jumlah `182 mm`; A4 | **Ukuran kod disahkan; bukan kelulusan semua pelajaran/semua laluan** | Jalankan sampel Word/PDF Tahun 2–6 mengikut laluan sebenar dan semak guru kanan/RTL tidak berkaitan |
| PPKI Pengurusan Kehidupan (penjana `staging/ppki/render_pengurusan_kehidupan.py`) | Menggunakan `_word` dan `_pdf` yang sama daripada DLP, warna PPKI berasingan | Jadual asas `182 mm` | **Ukuran kod disahkan; bukan kelulusan semua komponen/tahun** | Semak output sebenar Tahun 2–6 dan kotak guru kosong |
| Bahasa Arab Word READY Tahun 2–3 (`web/arabic_rph_word.py`) | Asal kepala guru kanan sahaja `3.25+5.5=8.75 cm`; tiga jadual bawah `18.7 cm` | PR pembetulan menggabungkan identiti pelajaran kiri dengan guru kanan dalam bingkai `3.25+5.5+9.95=18.7 cm` bagi 4 jadual | **PR #1197 MERGED dan Telegram Render LIVE pada 21 Nov 2026**; ujian fizikal A4/RTL lulus; muat turun Web sebenar belum disahkan | Luluskan CI Word+PDF A4 dan smoke laluan READY dahulu; jangan ubah fail DRAF Tahun 4–6 secara pukal |
| Bahasa Arab PDF | API Arab buat masa ini mengiklankan hanya `formats:["word"]`, dan ujian laluan mengharapkan PDF tidak tersedia | **Tiada PDF Arab sedia untuk pengguna** | **HOLD** | Jangan aktifkan sehingga fon/RTL, penghasilan PDF dan kualiti sumber disahkan |
| Sains SK | Ada pelbagai laluan penjana native dan ujian `test_sains_native_real_word_pdf_internal_20261108.py` untuk Tahun 2–6 | **Belum mengukur empat garis kotak pada keluaran sebenar terkini** | **BELUM DISAHKAN** | Jalankan QA bebas kuota dengan pembaca dokumen sebenar, simpan hasil struktur dan imej |
| Pendidikan Islam / Jawi | `tools/audit_pi_jawi_pdf.py` menyemak struktur A4 dan isi tanpa meluluskan bentuk huruf Jawi | **RTL/Jawi belum lulus bukti visual penuh** | **BELUM DISAHKAN** | Uji bentuk Jawi sebenar, arah kotak, A4 dan padanan Word/PDF tanpa mencampurkan susunan LTR |

## Peraturan audit seterusnya

1. **SATU REKA BENTUK KOTAK UNTUK SEMUA SUBJEK:** Semua kotak luar mesti sama lebar dan sejajar dalam setiap RPH. **Hanya Pendidikan Islam/Jawi dan Bahasa Arab/Arab menggunakan RTL** (arah label, penjajaran dan susunan kolum); **bukan** bentuk atau ukuran bingkai berbeza. Sains, DLP, PPKI dan subjek lain kekal LTR. Jangan paksa lajur dalaman sama lebar jika fungsinya berlainan.
2. Jangan keluarkan label **SIAP** daripada ujian kod semata-mata. Gunakan dokumen Word/PDF yang dijana oleh *laluan asal* dan semak visual A4; jangan tolak kuota guru untuk QA.
3. Jangan menjalankan penyeragaman automatik pada semua subjek khas: perubahan hanya selepas jurang sebenar dibuktikan, dengan regression SK/SP dan kandungan.
4. Untuk Bahasa Arab, RPH READY sahaja menerima pembetulan kanan atas; RPH DRAF menggunakan penjana staging lama dan mesti terus dianggap belum disahkan.

Audit ini rekod semakan sumber, **bukan pengesahan penerbitan Web atau semua kandungan PdP**.
