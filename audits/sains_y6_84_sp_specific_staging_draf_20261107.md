# Sains Tahun 6 — 84 RPH berasaskan DSKP 2021, semakan pedagogi awal

**Tarikh:** 7 November 2026  
**Status:** STAGING / HOLD, tiada deploy, tiada pindaan SQLite  
**Semakan:** kandungan SP DSKP secara editorial melalui salinan teks 2021, belum disahkan ahli panitia / bukti muka surat buku teks.

## Sumber yang dikenal pasti

1. DSKP Sains Tahun 6 KSSR Semakan 2017, edisi September 2021 (teks yang dibaca melalui FlipHTML5): https://fliphtml5.com/mcbrg/xizk/DSKP_KSSR_Semakan_2017_Sains_Tahun_6/. Laman ini ialah **salinan teks terbitan pihak ketiga**, bukan kelulusan sumber primer KPM.
2. Buku Teks Sains Tahun 6 SK KSSR Semakan 2017, terbitan DBP 2021, versi bacaan teks: https://anyflip.com/mcde/elam/basic. Penerbitan/edisi sepadan dengan buku KSSR Semakan 2017 yang dicari, tetapi **84 rujukan muka surat belum ditandakan verified** sehingga paparan buku tepat diperiksa satu demi satu; buku asal pengguna bersaiz besar belum diaudit penuh.
3. Ledger PdP staging daripada sumber asal v25.82 melalui `tools.audit_sains_342_pdp_release_gate_20261106.analyze()`; **bukan DB produksi**.

## Inventori 17 kumpulan SP

| Kumpulan SK | Bilangan SP/PdP | Reka bentuk aktiviti dan isu semakan |
|---|---:|---|
| 2.1 Pembiakan manusia | 4 | Rajah organ, urutan persenyawaan, penaakulan kepentingan, penerangan; hormati privasi, sesuai umur |
| 2.2 Sistem saraf | 6 | Pusat/periferi, fungsi otak/saraf tunjang, peranan isyarat, ramalan dan penjagaan; tiada ujian sakit |
| 3.1 Mikroorganisma | 6 | Lima kumpulan, ciri, proses hidup, faktor pertumbuhan melalui yis pembakar sahaja, manfaat/mudarat; tiada kultur tidak diketahui |
| 4.1 Interaksi haiwan | 4 | Mangsa-pemangsa, persaingan, mutualisme/komensalisme/parasitisme, penerangan interaksi |
| 4.2 Interaksi tumbuhan | 3 | Faktor persaingan tumbuhan, orkid/benalu dan pemerhatian simbiosis |
| 5.1 Pemeliharaan/pemuliharaan | 7 | Istilah, tindakan, spesies pupus/terancam, punca, kesan, penaakulan; status spesies semasa perlu disahkan dengan sumber |
| 6.1 Daya | 3 | Tarikan/tolakan, lima kesan daya, lakaran bukti |
| 6.2 Geseran | 5 | Definisi, kesan, eksperimen permukaan/jisim, solusi harian, laporan data |
| 6.3 Tekanan udara | 4 | Kewujudan, altitud, aplikasi, pemerhatian; elak kaca pecah |
| 7.1 Kelajuan | 5 | km/j, m/s, cm/s; eksperimen jarak/masa, rumus, takrif operasi, graf |
| 8.1 Kerosakan makanan | 3 | Foto ciri rosak, sebab mikroorganisma dan pemerhatian; tiada sampel berkulat hidup |
| 8.2 Pengawetan makanan | 7 | Tujuan, pengaruh faktor, projek selamat, gabungan kaedah, bekalan dan laporan; hasil projek tidak dimakan |
| 9.1 Bahan buangan | 6 | Bahan buangan, penguraian, pengelasan, amalan berhemah, kitar semula, 5R |
| 10.1 Gerhana | 5 | Simulasi gerhana Bulan/Matahari, cahaya lurus, ramalan, lakaran; **JANGAN melihat Matahari** |
| 11.1 Galaksi | 5 | Maksud, Bima Sakti, Sistem Suria sebahagian Bima Sakti, model skala, penerangan |
| 12.1 Kestabilan/kekuatan | 7 | Takrif, struktur, eksperimen luas tapak/ketinggian, bentuk/bahan, projek model, laporan |
| 13.1 Teknologi | 4 | Maksud, perkembangan bidang, manfaat/risiko, pemerhatian dan kesan terhadap kelestarian |

**Jumlah: 84 SP dan 84 PdP**, identiti `SCI-Y6-PDP-001...084`.

## Bahan staging yang dibina

- Tiga bank data aktiviti **ditulis khusus mengikut SP**, bukan template pelaksanaan AI masa nyata: `web/sains_y6_draf_bank_part1_20261107.tsv` (30), `part2` (33), `part3` (21).
- Pengesahan data: `web/sains_y6_84_activity_bank_draf_20261107.py` memeriksa 84 SP unik, tepat 17 kumpulan, aktiviti 1/2 tidak sama, BBM/PBD tidak kosong dan keselamatan bidang.
- Penjana: `tools/render_sains_y6_84_rph_draf_20261107.py` menghasilkan 84 Markdown, 84 Word dan 84 PDF, memelihara SK/SP/Unit/Tajuk/PdP sumber. Tidak menggunakan nombor muka surat buku teks yang diteka.
- Ujian sumber dan pedagogi: `tests/test_sains_y6_84_bank_quality_20261107.py`.
- QA cetakan fizikal Word: `tools/check_sains_y6_84_word_a4_20261107.py`, perlu satu halaman A4 dalam LibreOffice untuk semua Word. PDF juga perlu satu halaman A4 dan teks Aktiviti/PBD yang boleh diekstrak.
- Ledger teknikal semua **342** PdP dikemas kini dalam `tools/audit_rph80_sains_first_20261107.py`. Tahun 2:51, 3:45, 4:79, 5:83, 6:84. **Tiada skor akademik direka.**

## Gerbang akademik yang masih HOLD

Kiraan 84 draf lengkap secara teknikal **tidak** membuktikan sumber buku/halaman betul, RPT 2027 sejajar pada kelas sebenar, pembelajaran mencapai SP, pentaksiran PBD individu telah diluluskan, atau guru boleh muat turun melalui Web–Telegram pengguna. Aktiviti eksperimen mikroorganisma, pengawetan makanan dan gerhana memerlukan semakan keselamatan serta kebolehlaksanaan kelas.

Lepaskan bahan hanya apabila setiap PdP lulus **semakan halaman buku teks, kesepadanan SP penuh, bukti PBD guru/panitia, Word/PDF A4 dan ujian E2E Web–Telegram**, serta bukti rubrik setiap dimensi. Jangan mengubah status READY atau menganggap kualiti ≥80% daripada ujian teknikal.

**Semua RPH dan keputusan audit disimpan dalam GitHub staging, bukan pangkalan data produksi.**
