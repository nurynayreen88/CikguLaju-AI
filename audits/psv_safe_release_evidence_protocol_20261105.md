# PSV Tahun 2–6 — gerbang kelulusan selamat (5 November 2026)

**Status: STAGING DRAF. Tiada perubahan production, Telegram, pengguna atau rekod pembayaran.**

Pemeriksaan teknikal 210 RPH dan 20 pembetulan peta sumber telah lulus, tetapi dokumentasi terdahulu mengesan ketiadaan sijil visual per PdP dan tiada perkhidmatan Render khusus staging Telegram PSV. Oleh itu gerbang pada `web/psv_2027_rph_release_bridge.py` diperketat supaya **JSON kelulusan sahaja tidak mencukupi**.

### Semua gerbang wajib

1. **210 baris CSV audit unik** untuk Tahun 2–6 PdP 001–042. Setiap baris mesti mempunyai `Kelulusan_terbit=PASSED`; `Pemeriksaan_RPH_individu` mengandungi tiga token dipisahkan titik koma: `RPH_DIBACA;BUKU_TEKS_VISUAL_SAH;DSKP_SEMANTIC_PASSED`.
2. `Bukti_buku` mesti bermula `BUKU_TEKS_VISUAL_SAH:` dan menyatakan URL `https://` buku asal serta `ms ` yang benar-benar diperiksa. `Nota_semakan_terbuka` mesti kosong. Bukti tidak boleh direka daripada pembacaan teks unit sahaja.
3. `psv_release_approval.json` mesti menetapkan `audit_sha256` = SHA-256 *fail CSV tersebut* dan `content_sha256` = hash gabungan lima RPT CSV serta 210 RPH tepat daripada fungsi `_candidate_content_hash`. Jika satu dokumen berubah selepas semakan, kelulusan luput.
4. Semua 210 RPH dan RPT mengandungi status tepat `READY` setelah semakan visual, DSKP, kalendar dan QA guru selesai; jangan buat pertukaran status pukal sebelum bukti diperoleh.
5. `runtime_staging=PASSED` dengan `runtime_staging_commit` SHA 40 aksara daripada ujian **native Telegram staging sebenar**, termasuk Word, PDF, navigation, kelas/tarikh, entitlement/credit, dan subjek lain tidak berubah.
6. `CIKGULAJU_PSV_RPH_RELEASE_ENABLED=1` hanya digunakan pada perkhidmatan yang sudah lulus, selepas semua gerbang di atas dipenuhi.

Semua syarat dinilai semasa pemasangan adapter. Jika satu pun gagal, adapter **tidak dipasang** dan penjanaan produksi kekal tanpa perubahan. Ini **protokol kawalan release**, bukan sijil bahawa semua syarat sudah selesai. Fail kelulusan tidak diwujudkan dalam PR #267.

Perkhidmatan Render yang sedang wujud: staging web v1 masih branch `staging/cikgulaju-web-v1` dan bukan staging Telegram PSV; service LIVE `CikguLaju-AI` menggunakan `main` dan auto-deploy. Jangan ubah dua perkhidmatan itu atau gabung PR #267 secara automatik.
