# Integrasi Buku Aktiviti Sains Tahun 2–3 — staging sahaja

Tarikh audit: 7 November 2026. PR: [#442](https://github.com/nurynayreen88/CikguLaju-AI/pull/442). Semua bahan kekal **DRAF/HOLD**.

## Bahan asal yang telah ditemui dan diperiksa

| Subjek/Tahun | Pautan Buku Aktiviti SK | Halaman imbasan | Halaman Kandungan |
|---|---|---:|---|
| Sains Tahun 2 | https://drive.google.com/file/d/1j0qoRWHcaAzHVgbb6uua7k_3i2-qVm0v/view | 89 | PDF 3–4 (iii–iv) |
| Sains Tahun 3 | https://drive.google.com/file/d/1kVL3PT-VjQiITqmfNXlURQA8gLYvCrI5/view | 98 | PDF 4–5 (iii–iv) |

Kedua-duanya ialah buku aktiviti bercetak Sekolah Kebangsaan dengan logo KPM yang telah disediakan sebagai **imbasan**; tiada lapisan teks yang boleh dicari. Sumber disiarkan di portal Sekolah Kebangsaan Sultan Abu Bakar (1) dalam bahagian *BUKU AKTIVITI TAHUN 1–3*: https://www.sksab1.com/link.html.

**Perbezaan halaman**: Tahun 2 halaman PDF = m/s bercetak **+4**; Tahun 3 halaman PDF = m/s bercetak **+5**. Nombor dalam RPH merujuk halaman **bercetak**, bukan kedudukan PDF.

## Padanan kepada RPH

- **51/51 PdP Tahun 2**: `SCI-Y2-PDP-001` hingga `SCI-Y2-PDP-051` mendapat satu tajuk latihan khusus dan nombor halaman buku. Contoh: PdP 001 SP3.1.1 — *Pembiakan Manusia* m/s13; PdP 003 SP3.1.3 — *Mari Banding Beza* m/s17 (tumbesaran; **jangan gunakan latihan pewarisan yang tidak sepadan SP rasmi 3.1.3**); PdP 051 SP10.1.6 — *Model Binaan Saya* m/s84, tetapi DSKP asal masih ada konflik 'campuran'.
- **45/45 PdP Tahun 3**: satu latihan spesifik bagi setiap SP induk dan PdP. Contoh: PdP 026 SP6.1.6 — *Mengukur Isi Padu Pepejal Tidak Sekata*, m/s61; PdP 037 SP9.1.2 — *Suhu Planet*, m/s80; PdP 044 SP10.1.4 — *Model Takal Saya*, m/s90.
- Tahun 3 PdP 006 (3.2.1), 010 (3.3.1), 011 (3.3.2) mempunyai SP integrasi tambahan dalam staging. Padanan buku aktivitinya tertumpu pada SP induk, **belum bukti semakan latihan bagi SP integrasi**.
- Aktiviti utama RPH asal dipelihara. Buku aktiviti ditambah untuk tugasan pengukuhan/bukti PBD dengan arahan guru menyemak respons **setiap murid**. Muka surat dan nama latihan disertakan dalam RPH Word/PDF dan manifest, pautan PDF asal juga ada dalam Markdown/manifest.

## Perubahan fail, tanpa integrasi pengguna LIVE

- `audits/sains_y2_y3_buku_aktiviti_mapping_20261107.json` — **96** padanan ketat dengan kod PdP, SP, tajuk aktiviti bercetak, m/s buku, halaman PDF, URL buku, keadaan semakan.
- `tools/sains_buku_aktiviti_mapping_20261107.py` — gagal jika SP, tahun, ID, sumber atau halaman tidak sepadan. **Jangan guna fallback senyap ke latihan lain.**
- `tools/render_sains_y2_51_rph_draf_20261107.py` — tambah latihan BA Tahun 2 di RPH Word/PDF/Markdown dan manifest, tanpa menukar SP asal.
- `web/sains_y3_rph_activity_preview_20261106.py` dan `tools/render_sains_y3_45_review_pack_20261106.py` — tambah Buku Aktiviti Tahun 3 dan bukti PBD dalam 45 draf RPH.
- `web/sains_buku_aktiviti_resources_20261107.py` — mencadangkan **satu pautan buku aktiviti sebenar mengikut tahun** berserta halaman SP kepada menu Web/Telegram apabila diluluskan; `ready_for_runtime=False`. Tidak menghasilkan 96 PDF palsu atau rehos PDF asal tanpa hak.
- Ujian automatik memeriksa 96 SP, keunikan sumber, offset halaman, pemeliharaan RPH, serta muat turun berpautan. Semua pengguna LIVE dan DB kekal tidak berubah.

## Baki semakan akademik dan hak penggunaan

1. Isi sebenar setiap latihan dalam buku imbasan perlu diteliti oleh penyemak guru/panitia untuk padanan sepenuhnya terhadap SP — **jadual kandungan dan aktiviti yang dipilih ialah rujukan sah tajuk/muka surat tetapi status padanan SP masih cadangan**.
2. Semak SP3.1.3 Tahun 2 dan 10.1.6 Tahun 2 serta SP tambahan Tahun 3 secara khusus.
3. Sahkan penjana Word/PDF Tahun 2 (51 fail) dan Tahun 3 (45 fail) masih **satu halaman A4** selepas penambahan baris Buku Aktiviti; jika bertambah dua halaman, baiki susun atur dan jangan lepaskan.
4. Uji muat turun dengan akaun Web/Telegram staging dan penyediaan pautan pengguna. Pautan sumber yang dipautkan tidak bermaksud fail telah disalin atau tersedia pada pelayan CikguLaju.
5. Sahkan hak pengedaran jika mahu menyimpan salinan PDF dalam servis sendiri; buat masa ini **hanya pautan ke sumber asal**.

Sasaran kualiti **≥80% belum disahkan**. Tiada perubahan kepada SQLite pengguna, akaun, kuota, Render Telegram/Web produksi atau status READY.
