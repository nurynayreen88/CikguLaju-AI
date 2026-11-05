# RPH Matematik v38 — STAGING sahaja (Tahun 2–6)

**Status:** TEKNIKAL 585/585 LULUS; **BELUM FINAL READY akademik atau Telegram LIVE**.

Kod dalam cabang ini hanya menambah `staging_preview.py` dan ujian fail-closed; **tidak diimport atau dipasang oleh `app.py` atau `tools/run_telegram_with_curriculum_api.py`**. Tiada perubahan database, subscription, kuota, Telegram production atau `main`.

## Cara menguji pada runtime staging terasing (untuk pembangun sahaja)

1. Muat turun **ZIP v38 dari lampiran perbualan ChatGPT pemilik**, bukan GitHub public; simpan sebagai fail tempatan pada pelayan staging sahaja. SHA-256 yang diwajibkan:
   `29097e08da6b79ba1f3395defe03fbb0e02554bf58bcc794aeacc30a335558ad`.
2. Pastikan pengguna staging mempunyai `_access_info`, `_is_admin`, `send`, `send_document`, dan `callback` yang berasingan daripada produksi.
3. Pada staging **sahaja**, tetapkan `CIKGULAJU_MATH_RPH_V38_STAGING_PREVIEW=1` sebelum mengimport `staging_preview.install(ns, absolute_archive_path)`.
4. Untuk ujian callback, gunakan `mathrph_v38_preview_y2_l001_pdf` atau `mathrph_v38_preview_y6_l117_docx`. Callback lain didelegasikan tanpa perubahan. **Jangan tambahkan callback ini pada menu pengguna produksi.**
5. Uji `python -m unittest tests/test_matematik_v38_staging_preview.py` untuk pengawal tanpa asset, dan unit test lokal tambahan dengan ZIP sebenar untuk pembacaan 585/585, sebelum sebarang ujian Telegram staging. Ketika asset tiada, kod menolak permintaan tanpa mengambil fail dari lokasi lain.

## Gate penerbitan belum lulus

- **585 RPH individu** belum mendapat pengesahan aktiviti/PBD kepada halaman Buku Teks dan Buku Aktiviti yang berkaitan.
- **83 ID RPH Tahun 4 → 117 Lesson** mengandungi 34 sesi pecahan cadangan; perlu pengesahan kandungan setiap sesi.
- Pemetaan takwim 2027, cuti negeri/cuti ganti dan jadual kelas sebenar belum diluluskan.
- Penghantaran fail melalui **Telegram API sebenar**, penggunaan DB aktif dan regresi subjek lain belum diuji bagi v38.
- Jika mana-mana syarat gagal, **jangan nyatakan FINAL READY**; jangan merge ke `main` yang auto-deploy ke Render.

Laporan audit yang boleh diaudit: [v38 QA](https://github.com/nurynayreen88/CikguLaju-AI/blob/audit/matematik-evidence-gate-20261105/audits/matematik_v38_split_session_gate_20261105.md) pada cabang audit berasingan, [GitHub repo Math RPT](../../rpt_2027/matematik/README.md).


## Pembetulan v38
34 pasangan RPH sumber Tahun 4 dipisahkan kepada sesi asas/aplikasi: 34 Aktiviti 2 sesi pertama dan 34 pentaksiran sesi kedua dikemas kini. Tiga ayat objektif Tahun 4 turut dibaiki (Lesson 022–024). Pakej v38 ialah calon staging, bukan FINAL READY.
