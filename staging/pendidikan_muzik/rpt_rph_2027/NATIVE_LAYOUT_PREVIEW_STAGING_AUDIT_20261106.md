# Pratonton pemetaan 3 fasa Muzik → jadual RPH native Telegram (6 Nov 2026)

**Staging sahaja:** Modul `native_layout_preview_staging.py` ialah fungsi **baca sahaja** yang menterjemahkan RPH Muzik Markdown kepada struktur `telegram-native-rph-v1` untuk audit, **bukan** endpoint, bukan renderer, bukan perubahan Web/Telegram. Tiada fail Word/PDF dijana oleh modul ini.

Pemetaan pembelajaran:
1. **Set Induksi — 4 minit** → Fasa 1.
2. **Aktiviti 1 — 8 minit**, **Aktiviti 2 — 10 minit**, **Pengukuhan dan Penilaian — 6 minit** → Fasa 2, masing-masing kekal dengan label dan isi penuh. Digabung hanya kerana format native memerlukan 3 baris fasa.
3. **Penutup — 2 minit** → Fasa 3.
4. Tujuan, SK/SP, kriteria kejayaan (jika RPH menyebut), BBM dan pentaksiran → metadata jadual; refleksi/pemulihan → footer.

**Kawalan:** Modul menolak tahun di luar 2–6, PdP di luar 1–35, ID yang tidak padan dan aktiviti wajib yang kosong/berganda. Nilai `approved_for_live=False` sentiasa, sebab **tiada 175 DOCX/PDF sebenar dan tiada parity sumber Web–Telegram**. Kod SK/SP RPT asal dipelihara termasuk konflik Tahun 4; modul ini tidak 'mengesahkan' kod.

**Langkah masih perlu:** pemeriksaan teks lengkap/nota sumber dan kriteria kejayaan, sambungan subjek MUZIK ke `web/native_rph_telegram_api.py`/digest sumber yang sah selepas kelulusan, ujian generator native sebenar (175 Word dan 175 PDF) serta satu halaman A4 sebelum FINAL READY.
