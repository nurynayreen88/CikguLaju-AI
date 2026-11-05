# Pendidikan Muzik 2027 — Quality Gate dan Bukti Sumber
**Tarikh:** 5 November 2026  
**Branch:** `staging/pendidikan-muzik-dskp-rph-audit-20261105`  
**PR:** #335 (DRAFT, JANGAN MERGE)

## Hasil semasa
| Tahun | RPT 2027 draf | RPH PdP draf | DSKP SP diinventori |
|---|---:|---:|---:|
| 2 | 1 | 35 | 20 |
| 3 | 1 | 35 | 22 |
| 4 | 1 | 35 | 19 |
| 5 | 1 | 35 | 20 |
| 6 | 1 | 35 | 18 |
| **Jumlah** | **5** | **175** | **99** |

Fail RPT (.md/.csv), RPH setiap PdP (.md), manifest JSON di `staging/pendidikan_muzik/rpt_rph_2027/year{2..6}/`. Terdapat 190 fail kandungan berkenaan, semuanya **DRAF**. Sumber aktiviti RPH disusun mengikut domain kemahiran dan SP, **belum cukup bukti mengesahkan aktiviti buku teks setiap PdP**. Tidak boleh diterbitkan secara automatik.

## Pemeriksaan buku teks Tahun 4 — masalah sumber yang disahkan

`GuruBesar_BukuTeks_Pendidikan_Muzik_T4_SK.pdf` dalam folder Pendidikan Muzik Google Drive:
- Boleh dibuka dan diperiksa secara visual; PDF mempunyai **41 halaman, kebanyakannya imbasan muka surat bercantum dua halaman**.
- Halaman judul memaparkan **Pendidikan Muzik Tahun 4 Sekolah Kebangsaan**, edisi lama. Halaman awal menunjukkan topik **Terokai Muzik / Tinggi Rendah Bunyi Pic**, bukannya unit pembuka **Senja Nan Indah** daripada RPT 2025/26 yang dijadikan sumber.
- Oleh itu, buku tersebut **tidak boleh digunakan sebagai bukti pengesahan halaman buku teks bagi RPT Semakan 2017 ini**. Semua nombor halaman pada manifest masih label rujukan RPT lama; belum verified.
- Perlu mendapatkan buku teks Tahun 4 yang sepadan dengan RPT KSSR Semakan yang menggunakan *Senja Nan Indah, Warna-Warni Kek Cawan, Beg Cantik Menawan, Bunga Gergasi* dan seterusnya. Contoh daftar unit daripada koleksi rujukan [RPT 2024](https://app.testpaper.com.my/list_detail/gJ76/rph-dan-rpt-2024-pendidikan-muzik-tahun-4) / [RPT 2020](https://anyflip.com/edoh/qmnx/basic) ialah rujukan nama sahaja, bukan pengesahan keseluruhan buku teks.

## Konflik DSKP Tahun 4 — diperiksa pada PDF visual, bukan OCR
`GuruBesar_DSKP_Pendidikan_Muzik_Tahun_4.pdf`:
- PDF halaman ke-**38** (nombor bercetak **26**): SK **3.1 Pengkaryaan Muzik**, tetapi SP dicetak **3.2.1, 3.2.2 dan 3.2.3**.
- PDF halaman ke-**40** (nombor bercetak **28**): SK **4.1 Penghayatan Karya Muzik**, tetapi SP dicetak **4.2.1**.
- RPT rujukan menggunakan **3.1.x / 4.1.1**. Jangan normalisasi atau menimpa kod dalam DB tanpa semakan versi DSKP/DPK berkuasa. Manifest T4 merekodkan SP sumber RPT dan tanda konflik. Draf RPH yang ada bukan kelulusan kod.

## Isu kandungan lain
- Tahun 3: sebahagian tajuk/unit atau SP diulang dalam slot bersebelahan. Semak sama ada pengulangan PdP dirancang guru atau salinan berganda.
- Tahun 4: halaman Unit *Harum Mewangi* 50/52 daripada RPT lama telah dibetulkan berdasarkan buku Kesenian T4 sebenar kepada 100–103 bagi tiga PdP, masih perlu semakan kurikulum dan audio.
- Tahun 5: nama Unit 5 (*Raja di Lautan*) dan 9 (*Adiwira*) sudah ditemui dalam RPT 2026 awam, dengan 35 PdP disusun semula. Rujukan halaman dan audio masih belum disahkan pada buku asal.
- Tahun 6: salinan RPT lama menyebut **Baroque** sedangkan DSKP Tahun 6 **Classical**; julat rekoder DSKP meliputi C-D'.
- Tahun 2–3: rujukan Audio pada RPT tidak sama dengan bukti fail audio sebenar.
- Semua tahun: semak cuti negeri/cuti gantian Kumpulan A/B secara khusus; slot 2027 hanyalah cadangan.

## Ujian dan hasil
- GitHub tree readback: **175** fail RPH `rph_pdp_??.md`, **5** CSV RPT, **5** MD RPT dan **5** manifest unik.
- 5 manifest mempunyai **35 PdP** setahun, setiap satu dengan ID unik `MZ-Yn-xx`.
- Pakej Word/PDF untuk semakan guru telah dijana sebagai artifak perbualan ini (tidak dimasukkan ke GitHub): **5 RPT landscape** dan **5 buku RPH A4** yang masing-masing mengandungi **35 halaman untuk 35 PdP**. Dokumen diedarkan berlabel **DRAF**. Fail Word individu untuk 175 PdP turut dijana.
- Ujian `tests/test_pendidikan_muzik_rpt_rph_2027_staging.py` ditambahkan pada branch. **Ujian struktur asas sebelum pusingan Tahun 5 telah lulus dalam CI; kandungan Tahun 5 selepas pembetulan perlu ujian semula**.


## Pusingan tambahan Tahun 5 — semakan RPT sumber awam
- RPT 2026 Tahun 5 pada https://anyflip.com/eaqot/basd/basic dirujuk semula untuk menyusun 35 PdP dalam turutan sebenar, sambil mengekalkan ID `MZ-Y5-01` hingga `MZ-Y5-35`.
- Unit 5 ditetapkan **RAJA DI LAUTAN** dan Unit 9 **ADIWIRA**. Unit 9 dipadankan kepada PdP 27–29 dengan rujukan halaman 70–77 daripada RPT (masih belum semakan buku teks asal).
- RPT Tahun 5 kini hanya mempunyai **dua projek**, seperti struktur DSKP; projek ketiga yang dicadangkan sebelum ini tidak dikekalkan.
- 35 RPH Tahun 5 dijana semula dalam staging dengan kemahiran khusus nyanyian, perkusi, gerakan, rekoder, kreativiti, apresiasi dan projek. Ini pembetulan **kandungan draf**, bukan pengesahan akhir.
- Kod SP projek dalam sumber RPT dan DSKP tidak sepenuhnya sama; kod dalam RPH menggunakan DSKP Tahun 5, dengan nota audit sumber. PdP 31–32 ialah pemecahan latihan rekoder bagi blok RPT yang meliputi beberapa minggu, masih cadangan.
- Sumber teks penuh dan peta silang: `year5/RPT2026_SOURCE_CROSSWALK_AUDIT.md`.
- **PENTING:** Pakej ZIP Word/PDF daripada pusingan sebelumnya ialah snapshot lama dan belum menggambarkan pelarasan ini. Sebelum diedarkan kepada pengguna, perlu jana semula dan QA cetakan.

## Percanggahan jumlah projek tahun lain
- DSKP menyatakan Projek Seni Muzik dijalankan **dua kali setahun**. Manifest RPT Tahun 2, 3, 4 dan 6 sebelum ini menamakan projek ketiga berdasarkan RPT sumber lama / susunan draf. **Semak semula dan jangan anggap Projek 3 sebagai program rasmi sehingga sumber berkuasa disahkan.**


### Kemaskini buku teks sepadan — pembetulan penemuan asal
- Buku teks yang betul **telah ditemui dalam Google Drive**: `GuruBesar_BukuTeks_Pendidikan_Kesenian_T4_SK.pdf`, ID `1atgPcWpovM_In9W0EXTvWo2qBjZqRe5k`, DBP 2019, KSSR Semakan 2017.
- Buku **Pendidikan Muzik Tahun 4** yang diperiksa awal memang tidak sepadan, namun kesimpulan lama bahawa tiada buku sepadan dalam Drive kini tidak tepat; buku sepadan ialah gabungan **Pendidikan Kesenian**.
- **6 PdP Tahun 4 telah disemak terhadap kandungan halaman buku:** PdP 14/15/16 (Unit 5, halaman 50–53) dan PdP 31/32/33 (Unit 10, halaman 100–103).
- Unit 10 *Harum Mewangi* telah dibetulkan daripada rujukan RPT lama halaman 50/52 (sebenarnya Unit 5) kepada **100–101 (Kolattam)** dan **102–103 (Pergerakan Kolattam)**.
- Kod sumber RPT **4.1.1** dikekalkan sebagai `sp_rpt_source`; untuk aktiviti apresiasi, kod **4.2.1** yang dicetak dalam DSKP dan buku digunakan bagi dua PdP. Kod pergerakan **2.3.1** pada empat PdP ialah cadangan crosswalk kerana kod buku `4.2.2/2.2.7` berbeza daripada DSKP Muzik berdiri sendiri.
- Nombor Audio 44–48 dan 110–117 memang **dicetak dalam buku**, tetapi **fail audio/track tidak disahkan** dan tidak diaktifkan.
- Perincian: `year4/BUKU_TEKS_EDISI_SEPADAN_AUDIT.md`. Buku belum selesai diaudit bagi baki 29 PdP Tahun 4.


### Projek Seni Muzik dikawal untuk Tahun 2–6
- DSKP Pendidikan Muzik Tahun **2, 3, 4, 5 dan 6** menyebut **dua projek berskala kecil setahun**.
- Tahun 5: dua projek disusun berdasarkan RPT 2026 awam.
- Tahun 2, 3, 4 dan 6: 8 slot PdP hujung tahun yang sebelum ini dinamakan Projek 3 telah ditukar menjadi **cadangan pengukuhan/pentaksiran**, BUKAN projek ketiga rasmi. ID PdP tetap sama; label dan kod SP RPT asal dikekalkan dalam medan audit.
- RPH calon 34–35 untuk empat tahun tersebut sudah disesuaikan dengan kemahiran tahun. RPT/CSV setiap tahun turut diselaraskan.
- Semakan penerbitan masih diperlukan kerana slot pengukuhan adalah **cadangan**, bukan agihan rasmi RPT 2027; lihat `TWO_PROJECTS_PER_YEAR_AUDIT.md`.


## Audit buku 6 November 2026 — kemajuan berasaskan sumber
- **Tahun 4:** 22 PdP bertambah pemurnian teks buku, ditambah 6 PdP diperiksa kandungan halaman sebelumnya = 28/35; baki 7 PdP ialah slot projek/pengukuhan. Halaman penuh dan skor belum semuanya disahkan secara visual.
- **Tahun 5:** 15 PdP 12–17, 27–35 dimurnikan berdasarkan Buku Teks Muzik Tahun 5 DBP 2020; baki 20 PdP.
- **Tahun 6:** 7 PdP (11, 14, 15, 30–33) dimurnikan berdasarkan buku Muzik Tahun 6 DBP 2021; baki 28 PdP. Konflik julat Classical dalam DSKP (1750–1830) dan buku (1750–1850) didokumentasi, DSKP dijadikan rujukan standard.
- **Tahun 2:** 28/35 RPH mempunyai semakan teks buku, 7 RPH masih menunggu audit bukti setara (termasuk PdP 33 yang hanya draf); PdP 11 dibetulkan daripada halaman 32–33 kepada 36–37 kerana halaman asal berkaitan seni visual. **Tahun 3:** 11/35 RPH PdP 1–11 telah dimurnikan berdasarkan buku DBP 2018; 24 lagi menunggu audit individu.
- **Jumlah kemajuan semakan kandungan buku:** **89/175 semakan terhad**, bukan FINAL READY. **Tiada fail audio diperiksa** dan ZIP Word/PDF lama bukan snapshot terkini.
- Semua fail dan ujian kekal di staging. Lihat `SOURCE_BOOK_REGISTER_20261106.md`.

## Release gates
[ ] Buku teks sepadan dan nombor halaman disahkan PdP demi PdP  
[ ] Audio, skor atau muzik sebenar disahkan; jangan reka track  
[ ] Konflik DSKP/RPT Year 4 diselesaikan dengan sumber autoritatif  
[ ] RPT 2027 lengkap serta tarikh cuti negeri Kumpulan A/B disahkan  
[ ] 175 RPH dinilai kandungan satu persatu dengan evidens, bukan sekadar format satu halaman  
[ ] Ujian staging / pembaca Word-PDF / format Telegram sebenar lulus  
[ ] Selaraskan satu sumber generator antara Web dan Telegram  
[ ] Kelulusan penerbitan, checksum dan audit non-destructive sebelum `main`

**TIADA kemas kini** kepada `main`, SQLite produksi, Supabase pengguna, Telegram/Web runtime, akses pelanggan atau referral.


## Kemaskini tambahan 6 November 2026 — PdP 04–11 Tahun 3
- Buku Teks Pendidikan Kesenian Tahun 3 DBP 2018 penuh disemak **secara teks** pada halaman bercetak 18–21, 26–29 dan 36–39. **8 RPH Tahun 3** dibaiki berdasarkan aktiviti khusus buku, termasuk nyanyian *Kita Satu Keluarga*, pergerakan empat detik, *Tepuk Amai-amai*, *Putar-putar Roda Ciptaan*, tekstur lagu *Serangga*, kesan bunyi cerita *Gigih Si Labah-labah* dan Muzik Jaz.
- PdP 05 dan 06 kini berbeza: halaman **20** (latihan) berbanding **21** (persembahan tempo lambat/cepat). PdP 10 merujuk **Audio 39–40 bercetak**; Audio 36–38 asal tidak sesuai dan dipelihara dalam medan audit.
- Jumlah baharu: **Tahun 3 = 11/35**, **semua tahun = 89/175** semakan teks terhad; **baki 86 RPH** belum diaudit setara. **Tiada yang FINAL READY.**
- Kod buku gabungan Kesenian tidak disalin ke DSKP Muzik asal. Fail audio sebenar, skor visual dan Word/PDF masih belum disahkan. Nota perincian: `year3/BUKU_TEKS_8_RPH_TEXT_CROSSCHECK_20261106.md`.


## Audit tambahan Tahun 3 PdP 14–23 dan 27–31 (6 November 2026)
- **15 lagi RPH** disemak berdasarkan teks Buku Pendidikan Kesenian Tahun 3 DBP 2018: *Parang Ilang*, Gerak Irama, rekoder B/A/G, *Kad Ucapan Hari Lahirku*, *Irama Bingo*, *Selamat Malam*, *Boneka*, *Tamak Selalu Rugi*, apresiasi solo/koir dan *Seni Anyaman Jangan Dilupa*.
- PdP 14–17 dan 18–23 dipisahkan kepada aktiviti khusus buku; PdP 27 disahkan **Ajuk Nyanyianku** (Audio 65) dan PdP 28 **Boneka** (Audio 66–68), bukan Audio 69–70 (cerita). PdP 28 menggunakan buku halaman 81; asal 80–81 disimpan.
- **Kiraan semasa: Tahun 3 26/35 semakan teks; keseluruhan 104/175; baki 71 RPH menunggu semakan setara**. Semakan skor, fail audio, kod DSKP Muzik, Word/PDF masih belum FINAL READY. 
- Rujukan audit: `year3/BUKU_TEKS_15_RPH_TEXT_CROSSCHECK_20261106.md`. Jangan merge/deploy.


## Akhir sumber buku Tahun 3 — PdP 32–33 (6 Nov 2026)
- PdP 32 menggunakan *Permainan Buah Lazat* halaman 94–95: ciptaan corak **lapan detik** dengan minimum tiga ikon buah; Audio 75 tercetak.
- PdP 33 menggunakan *Muzik Rock* halaman 96: peranan penyanyi, gitar, bes, dram dan rock balada; tiada nombor trek dinyatakan.
- Tahun 3 kini **28/35** semakan teks buku; tujuh PdP projek/pengukuhan memerlukan audit kurikulum/pentaksiran berasingan. Keseluruhan **106/175** semakan terhad, **69** belum diperiksa setara. TIADA status FINAL READY.


## Pusingan 6 November 2026 — Tahun 5 PdP 01–11
- Buku Teks Muzik Tahun 5 DBP 2020, halaman 2–33 disemak secara teks untuk **11 RPH tambahan**, aktiviti spesifik ditulis semula.
- Pembetulan yang penting: *Da Dum* dinamik, Teroka Bunyi, ensembel Waspada Selalu, *Santun di Jalan Raya* dinamik/tempo, meter 3/4, *Busak Pakui*, rekoder *Lightly Row*, *Nama Berirama*, lagu berkembar dan permainan melodi 3/4 vs 4/4.
- **Tahun 5 26/35** semakan teks, **semua T2–6 117/175**, baki **58** semakan setara; **0 FINAL READY**. Audit lengkap: `year5/BUKU_TAHUN5_PDP01_11_TEXT_AUDIT_20261106.md`.
- Fail audio sebenar, skor visual, tarikh cuti negeri RPT 2027, pembaca Word/PDF dan integrasi Telegram/Web kekal blocker.
