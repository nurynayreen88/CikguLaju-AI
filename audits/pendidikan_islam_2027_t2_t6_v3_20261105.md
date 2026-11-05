# Pendidikan Islam Tahun 2–6 — Audit staging V3, 5 Nov 2026

**STAGING SAHAJA — DRAF, TIDAK BOLEH DEPLOY KE PRODUCTION.**

## Pakej sebenar yang disimpan
Library: `/CikguLaju/Pendidikan_Islam_2027_STAGING/CIKGULAJU_PI_2027_T2_T6_AUDIT_V3_PEMBETULAN_TERKAWAL_STAGING_20261105.zip`

SHA-256: `6e6ea026034885c80e1c45e4045bc3e26c439224484bb100a6fa41b213f27bae` (36,210,541 bait). **Fail ZIP ini disimpan dalam Library, bukan di GitHub.** Fail ini mengekalkan 696 RPH Word, lima RPT Word, lima RPT PDF V3 dan salinan sandaran lima PDF V2.

## Perubahan sebenar
- **104/696 RPH Word berubah secara terpilih**, 592/696 RPH tidak diubah daripada V2.
- **72 RPH Tajwid** dan **27 RPH Kefahaman**: penutup umum tasmi' diganti pentaksiran/rumusan khusus. RPH tasmi' dan tilawah kekal.
- T2 L056: salah taip `سورة سورة` dalam SP dibetulkan.
- T3 L065, T4 L061/L065, T5 L061/L065/L124/L128 serta T6 L065/L069/L124/L128: PBD untuk standard analisis diperkukuh. Objektif yang jelas di bawah aras standard diperbetulkan di tempat yang sah.
- T5 L061/L065/L124/L128: SK1.5 Tahun 5 ialah Surah **al-Asr** (DSKP KPM T5 halaman bercetak 23), bukan al-Qadr. RPT dan RPH diselaraskan.
- T6 L124: SK1.5 Tahun 6 ialah Surah **al-Ma'un** (DSKP KPM T6 halaman bercetak 23), bukan al-Asr. RPT dan RPH diselaraskan.
- T5 L069: jarak perkataan Jawi diperbetulkan. T6 L049/L097: pengulangan perkataan `مد` dibuang. T6 L137: pengulangan `سورة` dibuang.
- T6 L060: RPH alternatif solat ketika sakit dikemas kini mengikut SP4.2.3–4.2.5; objektif dan PBD kini menganalisis **tiga** kepentingan dengan sebab serta contoh. Bahan ini tetap berlabel cadangan CikguLaju, bukan RPT asal.
- T6 L006: sumber RPT 2026 tersalah 33–77; L006 33–51 dan L010 52–53 melengkapkan Surah asy-Syura yang mempunyai 53 ayat.
- T6 L117: az-Zumar 1–5 sememangnya sudah ada pada T5 L117, diteruskan hingga ayat 75 dalam T5 L121/L125/L129; gugur daripada sasaran T6 L117 yang bertema Juz29.

## QA yang benar-benar dijalankan
- Semua **696/696 RPH Word** unik, ada seksyen wajib dan kod SK/SP tidak bercanggah pada aras prefix.
- **104/104 RPH yang berubah** dieksport semula menjadi **satu halaman A4**; tiada blok teks terkeluar daripada sempadan PDF yang dikesan.
- Kelima-lima RPT PDF V3 bergabung muka depan asal dengan isi Word semakan V3; lanskap semua halaman dan **semua Lesson ID** hadir.
- Semua ZIP lulus CRC; audit 696 fail dan patch log dalam folder `AUDIT/`.

## Lapan pengecualian cakupan sumber (jangan diisi dengan tekaan)
| Lesson | Pengecualian |
| --- | --- |
| T2 L035 | Ayat al-Baqarah 224 berulang dalam dua Lesson RPT, niat pengulangan belum dapat diputuskan |
| T3 L145 | RPT Tahun 3 tamat Hud 88; tidak menjadualkan Hud 89–123 |
| T5 L141 | RPT Tahun 5 tamat Fussilat 20; tidak menjadualkan Fussilat 21–54 |
| T6 L014 | RPT tidak menjadualkan az-Zukhruf 74–89 |
| T6 L018 | RPT tidak menjadualkan ad-Dukhan 1–39 |
| T6 L026 | RPT tidak menjadualkan al-Jathiyah 34–37 |
| T6 L137 | Surah dinyatakan tanpa skop ayat berangka |
| T6 L141 | Surah dinyatakan tanpa skop ayat berangka |

Bukti tidak menyokong sebarang julat gantian. Setiap RPH yang menyalin julat asal sah pada skop Lesson itu sahaja; **status liputan tasmi' RPT keseluruhan masih perlu disahkan**.

## Release gate
**Tidak boleh merge ke `main`, tidak boleh aktifkan Telegram/Web, dan tidak boleh sentuh DB.**
Audit struktur dan 104 pembetulan tidak bermakna kandungan keseluruhan 696 RPH disemak baris-ke-baris oleh panel guru, atau dikalibrasi untuk semua jadual negeri. Sebarang klaim READY memerlukan pengesahan cakupan RPT, ketepatan seluruh Jawi dan bahan PdP setiap Lesson, serta ujian staging routing.

Sumber: RPT asal 2026 Tahun 2,3,5,6 dalam Drive; DSKP KPM Tahun 5/6 Apr 2019 p23, buku teks dan mushaf.
