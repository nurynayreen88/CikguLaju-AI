# CikguLaju Matematik Tahun 2–6 — v31 QA & FINAL READY Gate
**Tarikh:** 5 November 2026  
**Keputusan:** LULUS TEKNIKAL; **TIDAK FINAL READY AKADEMIK / TELEGRAM**.  
**Pengeluaran:** audit branch sahaja. Tiada merge, deploy, DB update atau perubahan RPH asal di main.

## Yang disahkan
- **585/585 Lesson** bagi Tahun 2–6 mempunyai calon RPH Word, Markdown dan PDF satu halaman A4; setiap tahun 117 Lesson.
- Semua **585 kod SP** telah dikesan dalam Buku Teks yang diakses. Bukti Tahun 5 Bahagian 1 diperoleh daripada laman PPD Batu Pahat / sumber sekolah KPM; 8 SP terakhir Tahun 5 Bahagian 2 didapati mengandungi fon terenkod dalam PDF dan disemak melalui halaman bergambar. Ini adalah **lokasi kod SP**, bukan automatik bukti ketepatan setiap aktiviti.
- **83 RPH v31 diperbaiki** dalam salinan calon: Tahun 2 = 23; Tahun 3 = 10; Tahun 5 = 43; Tahun 6 = 7. Tahun 4 v30 kekal selepas 61 teks terpotong telah dilengkapkan; 83 asal ↔ 117 Lesson masih perlu kelulusan akademik.
- Daripada 83 pembetulan: **37 RPH Tahun 5** (Lesson 068–104) merujuk latihan/cadangan pengajaran di Buku Teks Matematik Tahun 5 Bahagian 2 m/s 177–231; **46 RPH lain** disesuaikan dengan isi SP DSKP untuk menggantikan teks terlalu generik. Kedua-duanya ialah **calon kandungan**; jangan dakwa teacher-approved.
- Semua **83 RPH yang dikemas kini** berjaya dirender semula sebagai Word→PDF satu halaman. Kelima-lima set PDF gabungan Tahun 2–6 mengandungi 117 halaman setiap satu.
- Arkib v31 mempunyai **585 Word + 585 PDF individu + 585 Markdown**, lima PDF tahunan, laporan dan senarai QA; semua identiti tahun/Lesson serta bahagian wajib lulus ujian automatik.

## Gate masih terbuka
1. Audit individu akademik **585/585** masih belum dibuat/ditandatangani. Semakan kewujudan kod SP dan contoh dalam sebahagian halaman tidak menyamai audit satu persatu.
2. Semakan semula membuktikan **146 pengulangan set Aktiviti 1+Aktiviti 2+Pentaksiran** daripada baris sebelumnya dalam kumpulan kembar (T2 32, T3 19, T4 0, T5 26, T6 69). Pengulangan SP sama mungkin boleh diterima untuk ulang kaji, namun kumpulan merentasi SP/tajuk perlu ditulis berbeza dan disemak sumber dahulu.
3. Tahun 4 **83 RPH lama → 117 Lesson** masih mengandungi sesi pecahan cadangan yang belum dikaji secara individu terhadap RPH sumber, halaman Buku Teks/Buku Aktiviti dan instrumen pentaksiran.
4. Buku Aktiviti Tahun 2–6 dan setiap halaman yang benar-benar digunakan dalam pengajaran belum disahkan secara konsisten.
5. Kalender negeri, cuti umum/gantian 2027 dan keperluan masa 60 minit cadangan perlu diuji dengan jadual guru sebenar.
6. Telegram LIVE belum diuji untuk pilihan Lesson→RPH baharu menggunakan DB aktif, langganan/kuota dan ujian regresi tanpa mengubah data lama.

## Kriteria sebelum merge / penerbitan
- 585 baris audit individu (tahun/lesson/SP/BT-BA/perincian aktiviti/PBD/Word-PDF/rph runtime) mesti LULUS.
- Tiada pengulangan yang merentas SP atau tak sesuai tujuan sesi; sebarang ulang kaji perlu dilabel secara jelas dan mempunyai pentaksiran yang tepat.
- Uji enjin penjanaan sebenar pada staging dengan DB salinan/versioned; 585 sampel output serta akses Rakan Pembangun/langganan dan regresi subjek lain lulus.
- Buat backup & diff main semasa. Hanya selepas itu luluskan FINAL READY dan release terhad.

**Status rasmi: 585/585 QA teknikal lulus; 585 individu akademik belum lulus; FINAL READY = FALSE.**

Rujukan: [audit v30](./matematik_t2_t6_585_rph_v30_technical_qa_20261105.md), [repo PDF Matematik](https://github.com/nurynayreen88/CikguLaju-AI/tree/main/rpt_2027/matematik), [sumber buku Tahun 5](https://sites.google.com/moe-dl.edu.my/ppd-batu-pahat-sains-matematik/buku-teks-digital-bidang-sains-matematik/buku-teks-sekolah-rendah/matematik-tahun-5).
