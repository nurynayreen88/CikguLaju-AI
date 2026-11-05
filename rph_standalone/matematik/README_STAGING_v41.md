# CikguLaju Matematik v41 — ujian RPH staging

**INI BELUM FINAL READY.** Kod ini hanya menambah pratonton RPH bagi Tahun 2–6 dalam cabang staging dan tidak dipanggil oleh `app.py` atau Telegram production. `main`, RPT v28, DB pengguna, pembayaran, kuota percubaan dan bahan subjek lain tidak diubah.

## Aset input

Arkib `CIKGULAJU_MATEMATIK_v41_585_RPH_KANDUNGAN_DSKP_STAGING.zip` mengandungi 585 Word, 585 PDF satu halaman A4, 585 Markdown dan lima PDF gabungan. **Jangan muat naik ke GitHub public.** Simpan pada storan staging berasingan, dengan SHA-256:

`58e9f50701e26f318829f4730b38b20ae8eb4dbffb0e8b44987c315eab36bc89`

Fail `AUDIT/V41_RELEASE_GATE.json` mestilah menyatakan `lessons_total=585` dan `final_ready=false`; jika tidak, pemuat turun enggan mengaksesnya.

## Pengaktifan sengaja ketat

- Pada runtime **staging terpencil**, tetapkan `CIKGULAJU_ENVIRONMENT=staging` dan `CIKGULAJU_MATH_RPH_V41_STAGING_PREVIEW=1`.
- Panggil `install(namespace_runtime_staging, absolute_path_zip_v41)` secara eksplisit melalui harness staging. **Tiada import automatik dalam bot live.**
- Callback contoh `mathrph_v41_preview_y4_l023_pdf` atau `mathrph_v41_preview_y6_l019_docx`.
- Pratonton ini hanya membenarkan admin/pelanggan aktif (bukan membelanjakan 10 janaan percuma). Tiada bacaan/kemas kini Supabase; callback bukan pratonton diserahkan kepada handler asal.
- ZIP dinilai semula melalui hash dan diblok jika salah/tiada. Jika Telegram gagal mengesahkan penghantaran, jangan laporan berjaya.

## QA dan garis pemisah

- Ujian CI tanpa aset sulit: `python -m unittest discover -s tests -p 'test_matematik_v41_*.py' -v`.
- Pakej v41 tempatan: **585/585 PDF A4 satu halaman** dan **12/12 ujian dengan arkib sebenar lulus** pada 5 Nov 2026 (simulasi, bukan Telegram API).
- Audit DSKP asal: **593 kod SP dalam 585 Lesson ditemui**; 7 Lesson Tahun 4 memuatkan beberapa kod; Tahun 2 SP 4.1.1 dicetak `4. 1.1` dalam PDF.
- **Baki sebelum release:** semak individu aktiviti/PBD berasaskan BT/BA Tahun 2–3, pengesahan kandungan pecahan 83→117 Tahun 4, takwim 2027, DB staging, Telegram API sebenar serta regresi subjek lain.
- **Kelulusan separa yang dibenarkan:** modul pratonton dan ujian ini boleh digabung ke `main` sebagai **kod dormant/opt-in sahaja**, setelah CI berjaya, kerana ia tidak diimport oleh runtime produksi. **Ini BUKAN kelulusan 585 RPH untuk dipaparkan kepada guru**, dan tidak membenarkan pengaktifan callback, import ke app, penggunaan DB produksi atau deployment aset. Pengaktifan staging perlu token dan data ujian yang berasingan. Pelepasan kandungan RPH kekal disekat sehingga syarat akademik dan runtime lulus.

Laporan audit utama: [Matematik v41](https://github.com/nurynayreen88/CikguLaju-AI/blob/audit/matematik-evidence-gate-20261105/audits/matematik_v41_585_rph_release_gate_20261105.md).
