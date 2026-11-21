# SYARAT TETAP — Format RPH Premium CikguLaju

**Diluluskan oleh pemilik: 21 November 2026.**
**Status: WAJIB untuk semua RPH sedia ada yang disentuh dan setiap subjek/tahun/program baharu.**

Dokumen ini ialah kontrak reka bentuk dan penerimaan RPH Word/PDF CikguLaju, **bukan** arahan mengubah secara pukal atau menulis semula kandungan yang telah sah. Gunakan bersama \`AGENTS.md\`, fail konfigurasi \`docs/rph_premium_contract_20261121.json\`, dan ujian CI. Sebarang penyimpangan memerlukan keputusan pemilik serta rekod audit.

## 1. Ukuran dan susun atur yang mesti kekal

1. **Semua kotak utama dalam SATU RPH mesti mempunyai tepi luar kiri/kanan yang sejajar tepat**: kepala/identiti, maklumat PdP dan SK/SP, aktiviti, pemulihan/pengayaan serta refleksi. Pembahagian **lajur dalaman** boleh berbeza mengikut fungsi dan subjek. Jangan membesarkan satu jadual tanpa menyamakan yang lain.
2. Dokumen **A4**, margin profesional dan jadual formal dengan garisan kemas. Jangan potong isi untuk memaksa satu halaman; jika isi pelajaran yang sah memerlukan halaman tambahan, pastikan tiada teks terpotong, jadual tidak keluar margin dan sambungan kemas. Saiz fizikal Word dan PDF boleh berbeza kerana margin: wajib **sama lebar di dalam dokumen masing-masing**, bukan semestinya sama bilangan mm antara Word dan PDF.
3. **Kepala atas:** identiti subjek/tahun/tajuk di sebelah satu lagi, serta kotak **Kelas, Tarikh, Hari (jika wujud), Masa, Bilangan Murid** di **kanan atas** untuk susun atur LTR. Untuk Pendidikan Islam/Jawi dan Bahasa Arab/Arab, pelihara susunan **RTL** dan label dalam tulisan yang ditetapkan; jangan masukkan adapter LTR secara paksa. Kedudukan visual bagi setiap format khas mesti diuji tersendiri.
4. **Medan maklumat guru yang tidak diisi mesti kosong betul-betul**: tiada \`____\`, \`—\`, tarikh rekaan atau placeholder dalam medan Kelas/Tarikh/Hari/Masa/Bilangan Murid. Jangan kosongkan data yang memang pengguna sudah isi.
5. Pastel **lembut mengikut subjek**, tidak terlalu terang. Kotak, font, spacing, label, pemisahan aktiviti, dan warna kekal profesional. Aktiviti 1/2/3 berjudul **bold pada baris baharu**, diikuti ayat lengkap yang menerangkan tindakan guru dan murid.
6. Pastikan bahagian penting yang berkenaan tidak hilang: deskripsi **SK/SP** daripada sumber disahkan, objektif, kriteria kejayaan, pengetahuan sedia ada, BBM, EMK/Nilai, KBAT, PAK21, PBD/pentaksiran, set induksi, aktiviti, penutup, pemulihan/pengayaan dan refleksi **auto/manual**. Tiada label dalaman \`draf\`, \`produksi\` atau \`RPT\` yang tersalah dimasukkan dalam RPH pengguna.
7. **Word dan PDF mesti setara dari segi kandungan dan struktur utama**, walaupun kaedah pembinaan fail berbeza. Jangan mengubah arahan buku teks, SK/SP, susunan Lesson/PdP, pautan audio, atau kandungan asal hanya untuk membaiki bentuk.

## 2. Kontrak teknikal semasa (bukan pembenaran untuk override semua subjek)

- **Word native LTR yang diaudit:** sembilan subjek dalam \`docs/rph_premium_contract_20261121.json\`. Adapter yang sedia ada menyusun semula 3 jadual lama kepada **4 kotak**: kepala, maklumat PdP, aktiviti, refleksi. Lebar keempat-empat jadual disamakan berdasarkan kawasan cetak A4, maksimum \`10630\` twips untuk template tersebut. Tetapkan \`tblW\`, \`tblGrid\`, \`tcW\`, indent sifar dan penjajaran yang seragam. Simpan semua teks sumber.
- **PDF native LTR yang diaudit:** sembilan subjek yang sama. Bina kepala dua lajur dengan **objek Paragraph asal**. Lebar luar kepala, maklumat PdP, aktiviti dan refleksi ialah **172 mm** untuk template ini; sahkan koordinat garis yang betul pada PDF hasil render. **Jangan** padam/raster/overlay teks lama. Jika struktur sumber bukan 7 flowable dengan saiz jadual yang disahkan, pulangkan reka bentuk asal (fail-closed).
- **Format khas yang dilindungi:** Sains, DLP, PPKI, Pendidikan Islam/Jawi dan Bahasa Arab/Arab. Format asal yang sudah mendapat persetujuan tidak boleh ditimpa oleh adapter LTR. **Bukan bermaksud semua format khas sudah lulus audit lebar/semua kandungan.** Semak Word dan PDF satu demi satu sambil kekalkan RTL/LTR, label, struktur dan isi; betulkan hanya jika ada bukti perbezaan.
- **Pengembangan:** Untuk subjek baharu, cabang KSSR/KP2027, SJKC/SJKT, bahan PPKI/DLP dan mana-mana penjana Web/Telegram yang berbeza, syarat visual yang sama terpakai. **Jangan anggap lulus** semata-mata kerana subjek mempunyai warna pastel atau penjana umum telah LIVE. Daftarkan laluan dan keputusan audit, kemudian lakukan pembetulan yang khusus untuk penjana itu sahaja.

## 3. Pintu kelulusan sebelum sesuatu subjek/tahun/penjana ditandakan SIAP

- [ ] Kenal pasti penjana serta sumber kurikulum sebenar (Tahun/Subjek/Lesson/PdP/SK/SP dan buku/DSKP/RPT/SOW bila berkaitan).
- [ ] Jana **Word dan PDF sebenar daripada penjana berkenaan** atau ujian setara yang jelas dilabel sebagai ujian, termasuk satu contoh medan maklumat guru kosong. Jangan gunakan kuota pengguna untuk QA tanpa kebenaran.
- [ ] Periksa A4, keempat-empat tepi kotak (kedudukan kiri/kanan), kepala guru, panjang aktiviti, label/arah RTL dan warna. Contoh sukar/panjang mesti tidak terpotong.
- [ ] Bandingkan teks sebelum/selepas termasuk SK/SP, aktiviti, refleksi dan bilangan halaman yang wajar. Pastikan tiada penggantian kandungan atau pautan.
- [ ] Ujian automatik khusus lulus **dan** audit visual Word/PDF lulus. Kemas kini matriks audit/isu dengan bukti, lalu gabung PR.
- [ ] Sahkan Render deploy dan janaan/muat turun laluan pengguna yang berkaitan sebelum menulis **LIVE DISAHKAN**. Kod digabung ke \`main\` tidak sama dengan bukti semua laluan Web sudah LIVE.

## 4. Status pada tarikh syarat disimpan

- **Penjana native sembilan subjek LTR:** penambahbaikan kepala kanan atas dan kotak sejajar telah di-merge serta disahkan LIVE pada servis Telegram Render. Ujian automatik lulus. **Bukan** pengesahan untuk setiap laluan Web atau setiap Tahun/Lesson.
- **Sains, DLP, PPKI, Pendidikan Islam, Bahasa Arab:** format asal dilindungi; audit keseragaman Word/PDF dan contoh subjek masih **BELUM LENGKAP**.
- **Laluan Web alternatif:** berbeza mengikut \`selected.source\` (BM native, verified RPT master, Sejarah/RBT, sequence, English integrated, PPKI, SJKC/SJKT, provisional). Audit per-laluan **BELUM LENGKAP**; jangan guna label SIAP berdasarkan ujian penjana umum.
- Pusat penjejakan baki: GitHub issue **#1182**. Rekod status selepas setiap fasa dalam \`docs/LOG_KEMASKINI_BAHAN.md\`.

## 5. Peraturan masa depan

**Tidak boleh merendahkan piawaian ini apabila menambah subjek/tahun baharu.** Jika subjek baharu menggunakan template lain, templat itu perlu memenuhi *hasil visual dan kandungan* yang sama dengan cara selamat untuk bahasa/formatnya sendiri. Simpan dalam PR + CI + matriks audit sebelum penerbitan; jangan buat full replace atau operasi pukal yang berisiko pada RPH sedia ada.
