# Audit kesinambungan format RPH premium — subjek khas

Tarikh: 21 November 2026  
Piawaian wajib: [RPH Premium](RPH_PREMIUM_STANDARD_20261121.md)  
Penjejakan utama: [Isu #1182](https://github.com/nurynayreen88/CikguLaju-AI/issues/1182)

| Format / penjana | Keadaan sumber yang disemak | Ukuran / bentuk | Status bukti | Kerja lanjut |
|---|---|---|---|---|
| DLP Mathematics / Science (penjana `dlp_year2_rph.py`) | Kode Word/PDF menggunakan `_FIELD_WIDTHS=(48,134)`, `_ACTIVITY_WIDTHS=(32,122,28)`, panel tajuk `182 mm` (kini menggabungkan identiti kiri 118 mm + guru kanan 64 mm) | Semua jumlah `182 mm`; A4 | **PR #1206 MERGED, 10/10 CI LULUS, PENJANA RENDER LIVE**: pembina bersama Word/PDF diuji untuk laluan DLP sebenar Tahun 2–6; belum bukti muat turun akaun guru | Jalankan sampel Word/PDF Tahun 2–6 mengikut laluan sebenar dan semak guru kanan/RTL tidak berkaitan |
| PPKI Pengurusan Kehidupan (penjana `staging/ppki/render_pengurusan_kehidupan.py`) | Menggunakan `_word` dan `_pdf` yang sama daripada DLP, warna PPKI berasingan | Jadual asas `182 mm` | **PR #1206 MERGED, CI LULUS**: pilot PPKI dan muat turun PPKI Tahun 4–5 disahkan dalam ujian; penjana berasingan/klik guru belum disahkan | Semak output sebenar Tahun 2–6 dan kotak guru kosong |
| Bahasa Arab Word READY Tahun 2–3 (`web/arabic_rph_word.py`) | Asal kepala guru kanan sahaja `3.25+5.5=8.75 cm`; tiga jadual bawah `18.7 cm` | PR pembetulan menggabungkan identiti pelajaran kanan dengan guru kiri dalam bingkai `3.25+5.5+9.95=18.7 cm` bagi 4 jadual | **PR #1197 MERGED dan Telegram Render LIVE pada 21 Nov 2026**; ujian fizikal A4/RTL lulus; muat turun Web sebenar belum disahkan | Luluskan CI Word+PDF A4 dan smoke laluan READY dahulu; jangan ubah fail DRAF Tahun 4–6 secara pukal |
| Bahasa Arab PDF | API Arab buat masa ini mengiklankan hanya `formats:["word"]`, dan ujian laluan mengharapkan PDF tidak tersedia | **Tiada PDF Arab sedia untuk pengguna** | **HOLD** | Jangan aktifkan sehingga fon/RTL, penghasilan PDF dan kualiti sumber disahkan |
| Sains SK | Beberapa laluan penjana native; ujian sumber asal unit awal dalam `tests/test_sains_opening_real_word_a4_20261121.py` ditambah untuk Tahun 2–4 (#1208), kemudian Tahun 5–6 (#1209) | Audit automatik lebar luar tiga jadual Word, teks SK/SP dan PDF A4 untuk contoh PdP awal T2–T6 | **AUDIT SAMPEL AWAL DIKODKAN, #1208/#1209 MERGED**; bukan seluruh PdP, bukan semua laluan Web | Sambung sampel panjang dan semua laluan penjana; semak visual sebenar dan klik muat turun guru |
| Pendidikan Islam / Jawi | `tools/audit_pi_jawi_pdf.py` menyemak PDF struktur; ujian RTL Word→PDF sintetik fizikal ditambah #1210 | Kotak guru kecil di **kiri**, identiti besar di **kanan**; garis tepi luar dan teks A4 diperiksa melalui vektor PDF dalam fixture | **#1210 MERGED — SEMAKAN GEOMETRI FIXTURE SAHAJA**, bukan kelulusan bentuk huruf Jawi atau PDF native pengguna | Semak glyph Jawi, padanan teks, fail sebenar dan muat turun melalui akaun guru |

## Checkpoint 21 November 2026, 13:06 MYT — bukti dan had semasa

- **Sains SK Tahun 2–6:** PR [#1208](https://github.com/nurynayreen88/CikguLaju-AI/pull/1208) dan [#1209](https://github.com/nurynayreen88/CikguLaju-AI/pull/1209) digabung ke `main`. Skop ialah *contoh pembina asli unit awal* dengan pemeriksaan Word/PDF A4 dan penjajaran bingkai luar. Jangan tandakan keseluruhan 587 PdP atau semua laluan Web sebagai diaudit.
- **Pendidikan Islam/Jawi:** PR [#1210](https://github.com/nurynayreen88/CikguLaju-AI/pull/1210) digabung; uji koordinat vektor A4 bagi fixture RTL dengan guru kiri. Bukan bukti kelulusan bentuk huruf Amiri/Jawi atau muat turun PDF pengguna.
- **Galeri Web 16 contoh:** PR [#1204](https://github.com/nurynayreen88/CikguLaju-AI/pull/1204) digabung khusus ke branch `production/cikgulaju-web-20261105`; 16 halaman PDF diterbitkan melalui commit `6f1fb656e2133ce80d94ba101af7e309198bf367` dan deploy Render Web `dep-dc0ha5tjgj4s73as7iug` berstatus **LIVE** pada 21 Nov 2026 11:53 MYT. Pautan awam: `/contoh-rph-semua` dan `/contoh-rph-semua.pdf`. Ini **contoh ilustrasi format**, bukan 16 eksport daripada penjana pengguna. Semakan HTTP langsung dari luar Render dan ujian akaun guru masih belum disahkan dalam checkpoint ini.
- **Bahasa Arab:** fail Word READY Tahun 2–3 mempunyai semakan RTL sendiri, tetapi PDF Bahasa Arab untuk pengguna masih **HOLD**. Jangan pasang label PDF tersedia atau menukar arah susunan tanpa bukti.
- **Pintu penerimaan seterusnya:** bukti visual Word/PDF RPH sebenar bagi PI/Jawi, Sains, DLP/PPKI dan laluan Web khusus; padanan kandungan SK/SP, aktiviti serta lebar luar; akhir sekali klik muat turun dengan akaun guru tanpa menggunakan kuota untuk QA.
- **Pemisahan status:** kod gabung GitHub, deploy Render dan fail dimuat turun pengguna ialah tiga peringkat berasingan. Rekod di sini tidak mengisytiharkan semua subjek SIAP.

## Tambahan audit 21 November 2026 — semakan garisan fizikal PI/Jawi

- PR [#1212](https://github.com/nurynayreen88/CikguLaju-AI/pull/1212), merged `b436e03eb1d2186944168a4dcfdd9102cb0a4567`: alat `tools/audit_pi_jawi_pdf.py` boleh membaca garisan vektor PDF dan mengesan tepi kotak yang lari, termasuk kepala RTL yang dilukis sebagai segmen. Workflow `pi-jawi-pdf-audit` lulus.
- Hasil `grid_alignment.status` ialah `ALIGNED`, `MISALIGNED` atau `NOT_ASSESSED`; alat **tidak** menganggap PDF imej / tanpa garisan vektor sebagai lulus. Jalankan `python tools/audit_pi_jawi_pdf.py /path/to/rph.pdf --require-aligned-grid` untuk QA ketat. Status `structural_pass` lama sengaja kekal dan **tidak** membuktikan kotak sejajar.
- Ujian CI menggunakan fixture PDF sintetik, bukan dokumen PDF Pendidikan Islam yang dimuat turun oleh guru. **Sumber sebenar, glyph Jawi dan sambungan Web/Telegram masih memerlukan audit**. Keputusan geometri sahaja tidak boleh diberi label `LIVE DISAHKAN`.

## Peraturan audit seterusnya

1. **SATU REKA BENTUK KOTAK UNTUK SEMUA SUBJEK:** Semua kotak luar mesti sama lebar dan sejajar dalam setiap RPH. **Hanya Pendidikan Islam/Jawi dan Bahasa Arab/Arab menggunakan RTL** (arah label, penjajaran dan susunan kolum); **bukan** bentuk atau ukuran bingkai berbeza. Sains, DLP, PPKI dan subjek lain kekal LTR. Jangan paksa lajur dalaman sama lebar jika fungsinya berlainan.
2. Jangan keluarkan label **SIAP** daripada ujian kod semata-mata. Gunakan dokumen Word/PDF yang dijana oleh *laluan asal* dan semak visual A4; jangan tolak kuota guru untuk QA.
3. Jangan menjalankan penyeragaman automatik pada semua subjek khas: perubahan hanya selepas jurang sebenar dibuktikan, dengan regression SK/SP dan kandungan.
4. Untuk Bahasa Arab, RPH READY sahaja menerima pembetulan susunan guru di kiri/identiti di kanan; RPH DRAF menggunakan penjana staging lama dan mesti terus dianggap belum disahkan.

Audit ini rekod semakan sumber, **bukan pengesahan penerbitan Web atau semua kandungan PdP**.

## Penyelarasan penjana DLP/PPKI 21 November 2026 — batas bukti

- Penjana bersama `dlp_year2_rph.py`: PR #1206 (merged `main`) membina kepala **identiti kiri 118 mm + metadata guru kanan 64 mm** (jumlah 182 mm) dalam Word dan PDF; maklumat guru dikeluarkan daripada jadual SK/SP supaya tidak berulang. Semua jadual bawah kekal 182 mm; teks sumber SK/SP, aktiviti, bahan, refleksi tidak ditulis semula.
- PPKI pengurusan kehidupan *pilot* menggunakan pembina yang sama; **PPKI Tahun 3–6/komponen lain bukan automatik termasuk**.
- DLP lain Tahun 3–6 hanya terliput **jika** pemanggil sebenar menggunakan `_word`/`_pdf` yang sama; CI DLP Tahun 2–6 bagi laluan yang bersambung telah lulus; penjana DLP/PPKI selain pembina bersama belum disahkan.
- **CI 10/10 dan deployment penjana Render telah disahkan LIVE** (`dep-dc0hohtg1s2s73e3b110` pada 21 Nov 2026, 12:23 MYT). **Kekalkan BELUM DISAHKAN untuk klik muat turun akaun guru Web/Telegram dan penjana khas yang belum diaudit**; merge/deploy penjana bukan bukti semua RPH siap.
