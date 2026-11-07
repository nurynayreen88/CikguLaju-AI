# Sains Tahun 5 — audit 83 RPH khusus (staging, 7 November 2026)

**PR:** [#442](https://github.com/nurynayreen88/CikguLaju-AI/pull/442). **Status:** DRAF/HOLD; tiada penerbitan Telegram/Web, perubahan data pengguna atau kelulusan automatik.

## Bukti sumber

- Asal SK/SP: DSKP KSSR Semakan 2017 Sains Tahun 5, fail Google Drive pemilik: https://drive.google.com/file/d/1YkiK-pVo4UUzyOUvv_Vrico58eQyddCz/view. Kesemua 83 kod SP daripada turutan PdP v25.82 Tahun 5 ditemui dalam lapisan teks dokumen DSKP; semakan ini mengesahkan **kehadiran kod**, bukan semakan semantik keseluruhan 83 pernyataan.
- Buku teks Tahun 5: fail asal di Drive ialah bahagian pertama sahaja (m/s 1–35). **Tiga PDF sumber kini lengkap m/s 1–234 dan padanan token SP/halaman direkodkan 83/83**; lihat `audits/sains_y5_original_threepart_recovery_20261107.md` serta ledger hash `audits/sains_y5_83_full_textbook_printed_sp_pages_20261107.json`. Ini bukti kod SP pada halaman, bukan pengesahan kesesuaian semua aktiviti dan PBD.
- Nombor `SCI-Y5-PDP-001` hingga `SCI-Y5-PDP-083`, Unit 2–10, SK dan SP dikekalkan daripada senarai RPT/PdP staged v25.82; tiada penomboran semula.

## Kandungan dibangunkan

- Bank `web/sains_y5_83_activity_bank_draf_20261107.py`: 83 set aktiviti manual berbeza, satu setiap SP. Setiap satu mempunyai induksi, dua aktiviti guru/murid yang khusus, evidens PBD individu, alat dan keselamatan. Termasuk pernafasan/sistem badan, kemandirian haiwan, siratan makanan, pencaran biji, litar bersiri dan selari, suhu, pengaratan, jirim, fasa Bulan, buruj, dan mesin lestari.
- Pembetulan fakta dalam proses penulisan: **bonggol unta menyimpan lemak, bukan air**.
- `tools/render_sains_y5_83_rph_draf_20261107.py`: menjana 83 dokumen Word/PDF A4 dan Markdown apabila langkah CI berjaya. Format: `Aktiviti 1` dan `Aktiviti 2` tebal dengan nombor bermula pada baris baharu, tindakan guru dan murid, objektif/PBD, KPS serta refleksi.
- `tools/check_sains_y5_83_word_a4_20261107.py`: sahkan bilangan sebenar halaman Word selepas LibreOffice mencetak kepada PDF. Ujian PDF terus memeriksa satu halaman A4.
- KPS yang dipadankan ialah kod tahun 5 sebenar, termasuk **1.1.10 Mengawal pemboleh ubah**, **1.1.12 Mengeksperimen** (contoh untuk elektrik dan pengaratan), serta 1.1.6 Berkomunikasi.

## Isu penting yang sengaja dikawal

1. **Litar elektrik:** gunakan kit sel kering dan komponen yang sepadan. Tiada soket rumah, litar pintas atau bateri berlebihan. Ujian kecerahan mengubah satu faktor setiap kali.
2. **Haba dan air didih:** demonstrasi/rekod bacaan oleh guru; murid menafsir graf atau data; tiada murid menyentuh air mendidih atau pemanas.
3. **Pengaratan:** foto keadaan paku dan penyiasatan dikawal oleh guru, bukan membiarkan murid mengendalikan paku karat tajam.
4. **Fasa Bulan:** putaran/peredaran Bulan dan tempoh sinodik bulan Qamari tidak disamakan secara salah.
5. **KPS:** PdP bersifat penyiasatan mesti ada pemboleh ubah, ramalan, pemerhatian, rekod dan kesimpulan individu; semakan isi aktiviti sebenar masih perlu dibuat oleh guru sebelum penarafan 80%.
6. **Buku teks:** tiga bahagian lengkap (m/s 1–234); 83/83 kod SP sumber mempunyai padanan halaman, 103 halaman unik dengan token SP dan 16 sampel imej disemak. Kesemua 83 rujukan **belum diluluskan dari segi kesesuaian pedagogi/latihan**; semakan visual kandungan setiap PdP dan kesepadanan semantik DSKP masih diperlukan.

## Syarat untuk melepasi 80%

Ujian CI lulus sahaja tidak membuktikan kualiti pendidikan. Perlu ada semakan penuh 83/83 SP dan tajuk, halaman buku & latihan yang tepat, keberkesanan tindakan guru/murid, keselamatan eksperimen, bukti PBD, Word/PDF satu halaman yang boleh dibaca, kelulusan guru/panitia dan ujian laluan muat turun Telegram–Web staging yang menggunakan sumber sama. Skor tetap kosong sehingga bukti individu memenuhi rubrik 25+25+25+15+10 dan ambang minimum komponen.

**Jangan gabung atau deploy PR ini tanpa arahan seterusnya.** Tiada overwrite SQLite, Supabase, akaun, langganan atau kuota.
