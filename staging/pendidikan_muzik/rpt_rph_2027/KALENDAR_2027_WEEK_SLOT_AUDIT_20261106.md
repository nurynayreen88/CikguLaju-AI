# Semakan julat minggu RPT Pendidikan Muzik 2027 — 6 November 2026

**Pemeriksaan:** Semua 5 RPT CSV dan 175 manifest RPH Tahun 2–6 dibandingkan dengan indeks minggu induk CikguLaju 2027 Kumpulan A/B.

**Sumber induk (read-only):** [CIKGULAJU_RPT_2027_KALENDAR_CUTI_FINAL_VERIFIED — INDUK MINGGU RPT 2027 A B](https://docs.google.com/spreadsheets/d/1tf6-B6hmA4U6E0fCROcKpxh-B5uLUQOYBt6TZft_7_k/edit). Tab sumber mempunyai M01–M44 bagi setiap kumpulan dan 4 minggu cuti penggal penuh tanpa nombor minggu dalam setiap kumpulan. Fail JSON `KALENDAR_MINGGU_RPT_2027_INDUK_AUDIT_SNAPSHOT.json` ialah **snapshot audit**, bukan database pengganti.

**Keputusan pemeriksaan julat:** 175/175 manifest, 175/175 baris CSV, dan 35/35 PdP bagi setiap Tahun 2–6 **padan dengan sumber induk**. M10 bermula 14 Mac (A) / 15 Mac (B); M20 bermula 6 Jun (A) / 7 Jun (B); M32 bermula 5 September (A) / 6 September (B). Nombor minggu daripada sumber induk **bukan identiti PdP**: identiti sebenar ialah MZ-Y{tahun}-{PdP}.

**Had penting:** Pemeriksaan ini **tidak** mengesahkan setiap hari sebagai hari bersekolah. Cuti perayaan, cuti umum negeri, cuti gantian, aktiviti UASA/PBD dan jadual guru mungkin menjadikan sesetengah minggu mempunyai 0 hari PdP. Minggu bernombor induk tidak boleh digugurkan atau dianjak automatik kerana ketiadaan PdP pada satu negeri. Perlu padankan negeri, hari, jadual sebenar, dan sahkan sebelum RPH Hari Ini/RPT boleh auto-isi tarikh.

**Status:** LULUS padanan julat sahaja; **TIDAK FINAL READY**, TIADA perubahan pada tarikh pengguna atau produksi. Semua RPT 2027 masih DRAF.
