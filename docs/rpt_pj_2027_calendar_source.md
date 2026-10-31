# Sumber tunggal takwim RPT PJ 2027

Google Sheet: https://docs.google.com/spreadsheets/d/1tf6-B6hmA4U6E0fCROcKpxh-B5uLUQOYBt6TZft_7_k/edit

- Tab harian: `INDEKS PDP 2027 DIKIRA`, 5,840 baris (16 negeri x 365 hari).
- Kolum: Tarikh, Negeri, Kumpulan, Hari, Kategori Asas, Cuti Negeri, Cuti KPM, Cuti Gantian, Status PdP Asas, Status PdP Dikira.
- Gunakan **Status PdP Dikira**, bukan kiraan minggu generik, untuk memilih hari PdP.
- Semak tab `AUDIT FINAL 2027` dan `STATUS RELEASE 2027` untuk asal-usul sumber dan had warta.
- RPT PJ T4=34, T5=33, T6=34 PdP setiap negeri; 1,616 PdP keseluruhan.
- Kumpulan A: Kedah, Kelantan, Terengganu; negeri lain Kumpulan B.
- Cuti tambahan/peristiwa/cuti guru mesti disahkan dalam aliran RPH Minggu Ini; jangan ubah kalendar induk.
- Jangan gantikan data sedia ada atau ubah jadual pengguna; sebarang import perlu idempoten dan boleh diaudit.
- Fail Word v75 masih STAGING; pemetaan kandungan PdP-032 Tahun 5 ke buku teks asal masih perlu disahkan.
- Dokumen ini **penetapan sumber**, bukan bukti integrasi runtime, import DB atau deploy.

## Gerbang semakan sebelum RPT diterbitkan

- Tab `STATUS RELEASE 2027` merekodkan `FINAL VERIFIED — KPM/BKPP 2027`, tetapi tab `AUDIT FINAL 2027` masih mempunyai baris audit terdahulu bertanda `BLOCKED` / `SEMENTARA`. Gunakan baris `KEPUTUSAN AUDIT AKHIR` sebagai checkpoint sumber; jangan padam sejarah audit atau anggap semua risiko minggu PdP selesai.
- Tab `RISIKO MINGGU PDP 2027` menandakan minggu 7–12 Februari dan 16–21 Mei sebagai risiko kosong PdP mengikut negeri. Sebelum Word diterbitkan, uji per negeri terhadap `INDEKS PDP 2027 DIKIRA`; jangan alihkan atau gugurkan PdP secara automatik.
- Jadual RPT utama mengikut urutan PdP asal dan cuti penggal; cuti umum/negeri/perayaan boleh disenaraikan sebagai rujukan di bahagian akhir, bukan mengubah urutan PdP tanpa pengesahan guru.
- Kekalkan keluaran Word A4 landskap, muka depan dan fail berasingan Kumpulan A/B. Jangan tandakan fail READY sebelum padanan kandungan PdP, tarikh dan ujian Telegram disahkan.
