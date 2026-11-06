# Sejarah 2027 — 97 RPH dimurnikan, DRAF staging (6 November 2026)

**Skop:** PR #341. Pemurnian melibatkan 97 RPH yang sebelum ini mempunyai pembukaan Aktiviti 1 dan Aktiviti 2 berulang. Sebanyak 11 RPH awal yang sudah lebih terperinci dikekalkan.

**Perubahan:** Semua 97 RPH kini merujuk halaman teks bercetak yang tercatat dalam bukti sumber digital dan meminta murid memberi justifikasi berdasarkan bukti. Tugasan murid, objektif, kod SK/SP, masa 60 minit, nilai K, evidens PBD serta jadual RPT tidak diganti. Kandungan diselaraskan dalam 3 JSON sumber, 97 Markdown individu dan 3 HTML cetakan. Objek `page_specific_evidence` dilengkapkan bagi 97 rekod dengan status jelas **teks buku digital dipadankan dengan topik, bukan visual latihan**.

**QA berasingan:** `scripts/check_sejarah_crossformat_2027.py` menguji 108/108 RPH silang format JSON–Markdown–HTML, 97/97 arahan baharu, pautan sumber halaman dan pagar status draf. CI menguji semula Word/PDF dan penjana natif.

**Had kelulusan:** Ini pemurnian langkah guru, bukan salinan arahan buku teks sebenar. Semua 108 PdP **BELUM** mempunyai pengesahan visual latihan dan kelulusan guru; profil/logo sekolah serta ujian penghantaran runtime Telegram–Web masih perlu. Jangan buat perakuan palsu, jangan gabung ke `main` atau buka kepada pengguna.

**Rujukan tambahan:** DSKP KPM Tahun 4–6 dalam Drive (228 kod dan teks SP telah disemak secara bebas). ISBN DBP Tahun 4 dan Tahun 5 sepadan dengan katalog penerbit; sesi 2027 bermula 4 Januari bagi kedua-dua kumpulan seperti pengumuman KPM.
