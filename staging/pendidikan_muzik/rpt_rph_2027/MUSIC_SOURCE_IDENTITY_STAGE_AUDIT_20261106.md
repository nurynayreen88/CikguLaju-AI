# Sumber RPH Pendidikan Muzik: padanan identiti read-only staging (6 Nov 2026)

## Masalah yang dicegah

Penjana Telegram dan Web mempunyai deploy berasingan. Jika Web menggunakan RPH/manifest yang lebih lama, ia boleh menjana dokumen yang nampak betul tetapi salah padanan. `web/rph_shared_source_identity.py` sudah melaksanakan SHA-256 atas fail sumber tepat bagi subjek lain, namun `source_paths()` **belum menyokong MUZIK**.

## Penyelesaian yang disediakan dalam staging

Modul `music_source_identity_staging.py` membina **digest sumber sebenar untuk 175 PdP Tahun 2–6**, berdasarkan lima fail ini:

1. RPH PdP Markdown (kandungan aktiviti);
2. `pdp_manifest.json` tahun berkaitan (identiti PdP/SP/halaman/status);
3. CSV RPT Muzik 2027 tahun tersebut (tarikh kumpulan A/B);
4. `SUCCESS_CRITERIA_DRAFT_20261106.json` (81 cadangan, masih DRAF);
5. `KALENDAR_MINGGU_RPT_2027_INDUK_AUDIT_SNAPSHOT.json`.

Prinsip SHA-256 sama dengan sumber identiti Web: **path + NUL + bytes + NUL**, dibaca dalam urutan tetap. Tiada fail symlink, kosong, hilang atau melebihi had 2.5MB diterima. Kod tidak melakukan pengaktifan langganan, perubahan DB, Web, Telegram atau fail RPH.

## Gate release

- **Digest yang sama bukan bermaksud diluluskan.** Ia hanya membuktikan sumber fail sama.
- Pendaftaran MUZIK dalam router runtime dan whitelist penerima Web kekal tiada sehingga semakan kurikulum, Word/PDF sebenar berlapis dan kelulusan penerbitan lengkap.
- Ujian staging mesti membuktikan **175 ID unik**, padanan RPT–manifest, hash stabil apabila tidak berubah, hash berubah apabila RPH / CSV / kriteria berubah, serta **fail closed** jika fail dibuang/diubah menjadi symlink.
- Jika suatu hari Web/Telegram menggunakan digest ini, kedua-duanya mesti mempunyai **fail sumber identik**; jangan gunakan sandaran senyap jika tidak sama.

**Status:** reka bentuk kawalan sumber telah dibina untuk ujian staging, **TIDAK DILULUSKAN UNTUK LIVE**. Fail RPH dan manifest asal tidak diubah.
