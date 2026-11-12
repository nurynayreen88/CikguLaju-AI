# CikguLaju AI — Pusat Sehenti Digital Guru Sekolah Rendah
**Checkpoint: 12 November 2026 — STAGING / BELUM LIVE**

## Skop keputusan produk
- CikguLaju AI khusus **sekolah rendah Tahun 1–6**. Tiada sekolah menengah.
- Jenama memfokuskan PdP dan bahan mengajar harian, bukan dakwaan bahawa semua modul dirilis.
- Fungsi produksi sedia ada dikekalkan: RPH Hari Ini, Sediakan RPH, RPH Aktiviti Khas, RPT 2027, profil/jadual, Rakan Pembangun RM20, komen, admin dan referral persendirian.
- Jangan tambah menu PBD, UASA, BBM atau lembaran kerja berdiri sendiri sebelum sumber, endpoint, hak akses dan ujian siap.

## Perubahan dalam cabang ini
1. Ayat muka depan dan identiti portal jelas menyebut guru sekolah rendah Tahun 1–6.
2. RPH Hari Ini menunjukkan hasil sebagai pusat bahan PdP mengikut kelas tanpa mengubah urutan pilihan atau endpoint janaan.
3. rph-today.js mengenali **Student Book English Tahun 4 sahaja**, menggunakan URL PDF sumber dalaman yang disahkan oleh extra-materials (jenis student_book).
4. Penapis menolak sumber buku teks generik, pautan luar yang tidak disahkan, Student Book Tahun 3 dan Student Book bukan English.
5. Workbook English dan audio asal Muzik terus berfungsi secara berasingan.
6. Pemeriksaan metadata tidak mencaj kuota. Muat turun RPH masih menggunakan endpoint dan pengesahan kuota sedia ada.

## Kebergantungan release
- Backend Web English Tahun 4 Student Book dan link PDF **belum ada dalam cabang produksi yang menjadi base**. Ia berada di PR #559 (staging/web-english-y4-studentbook-20261111).
- Pasangan Telegram source-PDF berada di PR #558 dan pembetulan sumber Telegram lama di PR #567. Kebenaran pengedaran petikan buku perlu disahkan.
- Sehingga PR #559 serta prasyaratnya disatukan dan deployment/ujian live lulus, paparan Student Book baharu ialah **fungsi bersyarat**, bukan tawaran live. Tiada pautan rekaan atau fail buku penuh.
- Perlu ujian sebenar Web–Telegram pada akaun percubaan dan berbayar, pengesahan baki kredit tidak berkurang untuk semakan metadata/Workbook/Student Book, dan klik muat turun pada peranti mudah alih.
- **Jangan merge/deploy automatik**, jangan tukar akses atau harga, jangan buat migrasi Supabase, jangan keluarkan status READY berdasarkan ujian statik sahaja.

## Langkah seterusnya
1. Semak CI untuk kod dan aliran RPH Hari Ini sedia ada.
2. Selesaikan integrasi PDF English Tahun 4 bersama tiga PR sumber di atas.
3. Uji dengan guru sebenar: sesi buka web → pilih slot → dapat bahan → berjaya muat turun, dan rekod punca pengguna berhenti sebelum log masuk / sebelum janaan (tanpa data murid).
4. Selepas penggunaan harian stabil, keutamaan kandungan seterusnya ialah **bank lembaran kerja yang benar-benar siap dan berpaut pada Lesson/PdP**, bukan menu kosong.
