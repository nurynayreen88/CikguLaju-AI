# Audit lanjutan PJPK 2027 — Buku Teks Tahun 5–6 dan PdP 033 (4 November 2026)

## Sumber primer
- [DSKP PJPK Tahun 6, BPK 2021](https://drive.google.com/file/d/1AK0F5GLkhTkAPyhNkFBG6sHP6JgAU3Jv/view)
- [Buku Teks PJPK Tahun 5, KSSR Semakan 2017](https://drive.google.com/file/d/1M1kVxL7sliEUbi9vuuZ6llRVtmPjBuJE/view)
- [Buku Teks Pendidikan Jasmani Tahun 6](https://drive.google.com/file/d/1Y87xc3kHS4D0mSRxNQ8syYS8B-Y9CVmZ/view)
- RPT 2027 dan RPH asal pada `main` sebelum pembetulan melalui PR ini.

## Bukti semakan halaman calon (31 rekod)
Halaman ialah **nombor bercetak pada buku**, bukan nombor halaman PDF. Halaman sasaran telah diperiksa pada imej PDF buku asal; ini pengesahan **tajuk/halaman**, bukan pengesahan semantik keseluruhan SK/SP atau kelulusan guru.

**PJ Tahun 5 — 28 rekod**
- PdP 001–008: m/s 2, 3, 4, 5, 6, 7, 8, 9.
- PdP 009–010: m/s 12–13; PdP 011–012: m/s 16–17.
- PdP 014: 19; 015: 22; 016: 23; 017: 24–25.
- PdP 018: 28; 019: 29; 020: 30; 021: 31.
- PdP 022: 34–35; 023: 36–37; 024: 38–39; 025: 40–41.
- PdP 026: 42–43; 027: **44–46**; 028: 54–55; 032: 60–61.
- **Pembetulan substantif:** julat calon lama PdP 027 ialah 44–47; halaman bercetak 47 sudah memulakan unit Asas Akuatik, bukannya “Lemparan Ajaib”. Julat yang sesuai ialah 44–46; halaman 46 ialah latihan Uji Minda berkaitan balingan.

**PJ Tahun 6 — 3 rekod**
- PdP 032, kelenturan: m/s 74–75.
- PdP 033, kesihatan dan BMI: m/s **78–79**; RPH asal pernah menulis calon m/s 69, yang tidak sepadan.
- PdP 034, SEGAK: m/s **80–81**.
- Pada buku m/s 78, penanda SP mencatat `3.5.1, 4.5.1, 5.1.1`; pada m/s 79, `3.5.1, 4.5.2, 5.3.2`. Padanan PdP 033 dipilih daripada kandungan `3.5.1`, `4.5.1`, `4.5.2`, `5.3.2` yang dapat diajar secara bersepadu, tanpa memaksa semua kod halaman ke dalam satu sesi.

## Penyelesaian konflik PdP 033
- `5.2.2` **memang wujud** di bawah SK `5.2` dalam DSKP Tahun 6: usaha melakukan aktiviti fizikal untuk mencapai matlamat. Kesilapan RPT lama ialah memasukkannya di bawah senarai SK `3.5, 4.5, 5.3`.
- Oleh sebab PdP 033 berpaksikan komposisi badan dan penyakit hipokinetik pada buku m/s 78–79, SP `5.2.2` tidak dipaksa pada sesi ini. SK kekal `3.5, 4.5, 5.3` dan SP diselaraskan kepada `3.5.1, 4.5.1, 4.5.2, 5.3.2`.
- RPH dirangka semula: pengukuran sulit, tafsir BMI secara tertutup, langkah pencegahan penyakit hipokinetik dan perbincangan yang menilai `5.3.2`, tanpa mempermalukan murid.
- **Status:** `DRAF_CADANGAN`, `ready:false`, bukan READY.

## Baki sebelum READY
1. Audit semantik semua PdP (bukan sekadar kewujudan kod), termasuk halaman buku PJPK lain yang sudah dicatat lebih awal — tidak diluluskan automatik.
2. Semak jadual sebenar, takwim negeri/cuti dan aspek keselamatan aktiviti serta pengesahan guru.
3. Jana dan sahkan konsistensi 5 PDF + 5 Word; pastikan fail binaan benar-benar berada pada branch yang akan digabung.
4. Uji penghantaran **Telegram sebenar** untuk akaun berbayar/admin dan akses pengguna biasa; ujian unit semata-mata tidak dianggap bukti penghantaran.

Tiada perubahan diminta atau dibuat pada DB pengguna, kredit atau langganan. Semua status READY kekal palsu. Semakan buku teks Tahun 5/6 ini khusus kepada **31 rekod calon yang dikenal pasti**, bukan pengesahan keseluruhan buku atau semua 339 PdP.
