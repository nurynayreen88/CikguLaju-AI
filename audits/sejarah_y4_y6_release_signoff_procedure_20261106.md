# Prosedur pengesahan FINAL READY Sejarah Tahun 4–6 (2027)

**Perhatian: semua 108 PdP masih DRAF / belum diluluskan guru.** Dokumen ini ialah prosedur pelepasan, bukan kelulusan.

## Bukti minimum bagi setiap PdP

1. Semak teks dan **imej asal aktiviti halaman buku teks** DBP mengikut ISBN yang disahkan. Catat halaman tepat, langkah latihan, URL/fail bukti dan apa-apa perbezaan edisi. Catatan "julat unit" atau ringkasan teks digital **bukan** bukti visual latihan.
2. Semak kesahihan fakta sejarah, contoh, objektif, langkah guru/murid, penilaian PBD, kod SP/kewarganegaraan dan keselamatan privasi murid. Semak kajian kes sebagai **cadangan guru**, bukan kod aktiviti rasmi yang direka.
3. Semak RPH Word/PDF satu muka A4, RPT kumpulan A/B landskap dan kesan cuti umum/gantian negeri kepada jadual kelas sebenar.
4. Sahkan logo/nama sekolah/profil dan output **penjana natif** Telegram–Web untuk pelajaran yang sama; banding fingerprint sumber.
5. Dapatkan identiti penyemak, tarikh, bukti visual, keputusan dan pembetulan bertulis.

## Pengaktifan satu PdP, hanya selepas semua bukti sah

- RPH sumber `rph_standalone/sejarah/y{year}_2027_rph_DRAF.json`: tandakan `teacher_approval=true`, `textbook_page_verified=true`, `textbook_reference.exact_activity_page_confirmed=true`, `status=FINAL_READY`. Sediakan `release_signoff.approved_by`, `word_pdf_layout_verified=true`, `web_telegram_parity_verified=true`. **Jangan** cipta tanda lulus tanpa bukti.
- RPH Markdown individu `rph_standalone/sejarah/tahun_{year}/RPH_SEJ-T{year}-PDP-{nnn}.md`: semak kandungan sama, dan ubah baris status kepada tepat `**Status:** FINAL_READY`. Kemas kini penerangan DRAF lama supaya tidak mengelirukan guru.
- Baris RPT CSV yang **sama** sahaja: sahkan jadual dan jadikan `Status=READY`. Jangan ubah status 35 PdP lain.
- Manifest kelulusan bebas `audits/sejarah_y4_y6_release_approval_manifest_20261106.json`: rekod `exact_textbook_exercise_page_verified=true`, `teacher_individual_signoff=true`, `school_profile_logo_verified=true`, `telegram_web_native_parity_verified=true`, `release_ready=true`, `teacher_approved_by`, `textbook_evidence_url` serta maklumat sokongan.
- **Setelah semua kandungan, flag dan baris RPT di atas lengkap**, hitung `web.sejarah_2027_source_hash.fingerprint(year,pdp)`, lalu masukkan hash yang sama ke `rph.release_signoff.approved_source_fingerprint` dan `manifest.lessons[...].approved_source_fingerprint`. Ruang hash pada RPH dikecualikan daripada input hash untuk mengelak rujukan kendiri, tetapi semua medan lain termasuk nama penyemak masih dilindungi.
- Jalankan semua QA dan ujian fail Word/PDF sebelum membuka akses kepada PdP berkenaan. Sistem akan menolak semua yang belum lengkap.

## Pelindung teknikal selepas pembetulan

- Cap jari kini khusus kepada **baris JSON PdP**, Markdown individu, **baris RPT PdP** dan sumber DSKP/buku/kalendar yang sama. Meminda pelajaran lain tidak membatalkan cap jari PdP ini.
- Ujian `scripts/check_sejarah_fake_ready_gate_2027.py` menggunakan **kelulusan palsu dalam direktori sementara** bagi mengesahkan proses kelulusan boleh dicapai; ia bukan kelulusan untuk sekolah atau bahan sebenar.
- `scripts/check_sejarah_hash_stability_2027.py` menguji perubahan kandungan, hash kendiri, perubahan RPT dan pemisahan pelajaran.
- `scripts/check_sejarah_release_gates_2027.py` dan `scripts/check_sejarah_native_delivery_gate_2027.py` mesti menunjukkan **108/108 draf ditolak** selagi kelulusan sebenar belum wujud.
- Render A4 berasingan dan ujian fungsi Word natif ialah kawalan format. Kejayaan format **tidak** menggantikan pemeriksaan kandungan buku teks dan guru.

## Pelepasan akhir

PR #341 masih DRAF staging. Jangan gabung ke `main` atau hidupkan Sejarah Telegram–Web berdasarkan QA automatik sahaja. Sebelum pelepasan, pastikan keputusan penyemak dan dokumen Word/PDF natif yang sebenar lulus, tiada ujian regresi subjek lain gagal, dan tiada jadual pengguna atau data pembayaran disentuh.
