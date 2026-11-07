# Sains Tahun 2 — Audit dan pemurnian 51 PdP (7 November 2026)

**Lokasi:** `staging/rph80-audit-sains-first-20261107` / PR #442  
**Status:** DRAF / HOLD. **Belum mencapai 80% kualiti yang boleh diperakui** kerana pengesahan buku teks secara visual, kelulusan guru dan ujian akses end-to-end masih terbuka.

## Sumber asal yang digunakan

- DSKP Sains Tahun 2 KSSR Semakan 2017 dalam Google Drive pemilik: https://drive.google.com/file/d/1rr4CjNvhtI13ioiVSTZi65cvap7j1U6Z/view
- Buku Teks Sains Tahun 2 dalam Google Drive pemilik: https://drive.google.com/file/d/1LkJJWUb-zyFJ1ftpHM-4HIpIcEGLORI9/view
- Nombor PdP/SK/SP/Unit dari `v25.82` melalui sumber terjana 342 baris Tahun 2–6. Rekod sumber kekal tanpa pindaan.

## Hasil baharu

- **51 aktiviti RPH yang berlainan** dalam `web/sains_y2_51_activities_draf_20261107.py`. Setiap PdP ada dua aktiviti (peranan guru dan murid), objektif, PBD individu, bahan dan keselamatan. Tidak menggunakan API generatif ketika guru membuat RPH.
- Penjana `tools/render_sains_y2_51_rph_draf_20261107.py`: menghasilkan **51 Markdown + 51 Word + 51 PDF** (jika CI berjaya) daripada kod PdP asal. Setiap fail DRAF jelas, tidak diimport ke runtime atau DB pengguna.
- `audits/sains_y2_51_book_text_page_cues_20261107.json` — **51 petunjuk muka surat bercetak** dihubungkan dengan label SP dalam teks PDF Buku Teks asal. **Tiada satu pun disahkan secara visual sebagai halaman latihan yang sepadan.** Penjana menyatakan nombor tersebut sebagai *calon*, bukan halaman rasmi yang sudah disahkan.
- QA struktural mengesan sumber hilang, tajuk/SP tidak selaras, aktiviti yang sama, ujian keselamatan dan tiada sandaran guru. Word sebenar perlu diuji untuk satu halaman A4 melalui LibreOffice dalam CI.

## Isu akademik yang ditemui

### Tahun 2 PdP 003 — SP 3.1.3

Rekod PdP staging asal mengandungi tajuk **pewarisan ciri ibu/bapa**, tetapi dalam DSKP asal, **3.1.3 ialah perbezaan tumbesaran antara individu**. Pewarisan diterangkan di SP 3.1.4 dan 3.1.5, serta penerangan pemerhatian di SP 3.1.6. Susunan sumber asal 51 PdP hanya menyertakan 3.1.1, 3.1.2, 3.1.3 bagi Unit Manusia dan belum memetakan 3.1.4–3.1.6 sebagai PdP individu.

**Pembetulan selamat:** jangan ubah SP atau identiti sumber secara senyap. RPH PdP 003 di staging memfokuskan bukti perbezaan tumbesaran berdasarkan data murid *rekaan* dan diberi label **cadangan pembetulan**. Kandungan pewarisan 3.1.4–3.1.6 mesti diluluskan dalam perancangan PdP individu/terintegrasi tanpa mencipta kod SP rasmi.

### Tahun 2 PdP 051 — SP 10.1.6

Dalam dokumen DSKP asal, kod 10.1.6 di **Unit 10: Set Binaan** masih menggunakan perkataan **campuran** dalam teks pemerhatian, walaupun jadual standard prestasi dan konteks aktiviti menyentuh binaan.

**Pembetulan selamat:** simpan teks DSKP sebagai fakta sumber; RPH draf hanya mencadangkan galeri/penerangan model binaan kerana konteks unit dan buku teks. Ia **bukan pembetulan teks DSKP** dan tetap HOLD sehingga disemak oleh guru/panitia.

## Keselamatan & mutu

- Litar elektrik: hanya sel kering, larangan sambungan soket dan litar pintas, putuskan litar selepas digunakan.
- Campuran: tiada merasa/memakan sampel atau air panas; elakkan bahan tajam.
- Pertumbuhan manusia: profil rekaan, bukan perbandingan berat atau saiz tubuh murid sebenar.
- Biji benih: elakkan sentuh kulat; jadual data dan KPS yang spesifik.
- Terang/gelap: lampu suluh LED, bukan nyalaan api; bukan gelap sehingga mengundang bahaya.

## Pintu pelepasan belum selesai

1. Sahkan setiap petunjuk muka surat 51 PdP pada **imej halaman buku sebenar**, bukan lapisan teks sahaja.
2. Sahkan 3.1.3 dan liputan 3.1.4–3.1.6; dapatkan keputusan mengenai 10.1.6 dengan panitia/guru.
3. Uji setiap RPH 51 Word dan PDF satu halaman A4 selepas perubahan terkini.
4. Semak kandungan objektif, arahan guru/murid, kemahiran proses Sains dan PBD individu oleh penyemak akademik.
5. Uji aliran muat turun Telegram–Web staging daripada sumber yang sama sebelum apa-apa pelepasan.
6. **Jangan membuat dakwaan pencapaian ≥80%** sehingga semua semakan individu dan skor rubrik dengan bukti lengkap.

Tiada perubahan kepada `main`, produksi Telegram/Web, SQL, kuota percuma, pembayaran atau akaun guru.
