# Sejarah 2027 — kawalan kelulusan bebas, fail-closed

Tarikh: 2026-11-06. Digunakan hanya di staging PR #341.

Semakan sebelum ini telah menjalankan 108/108 RPH Word satu halaman dan RPT Word/PDF. Walau bagaimanapun ujian format **bukan** pengesahan kandungan, halaman aktiviti buku teks atau kelulusan individu.

Laluan `web/sejarah_2027_staging_source.py.lesson()` kini meminta **kedua-dua** bukti kelulusan dalam RPH dan rekod kelulusan bebas `audits/sejarah_y4_y6_release_approval_manifest_20261106.json` sebelum menyerahkan sumber bagi eksport natif. Rekod mesti dipadankan mengikut ID tahun/PdP/SK/SP dan mempunyai kelulusan guru, pautan bukti buku, semakan logo profil, pariti Telegram–Web, serta fingerprint SHA-256 sumber yang tepat. Menukar perkataan status kepada FINAL_READY secara tersendiri tidak membolehkan eksport.

Ujian semula mencuba mengubah `teacher_approval`, `textbook_page_verified`, `release_signoff`, dan `status` pada RPH sementara (bukan rekod aktif). Tanpa bukti bebas, `lesson()` mesti menolak permintaan. Tiada pengubahsuaian kepada pengguna, produksi atau DB.

**Baki:** Semakan buku teks dan aktiviti halaman untuk 108 PdP, kelulusan guru individu, ujian penjana natif dan suntikan logo profil. Semua masih DRAF. Rekod kelulusan tidak diisi secara automatik.
