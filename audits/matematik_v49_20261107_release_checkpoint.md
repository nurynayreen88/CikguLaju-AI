# Matematik v49 — audit lanjutan 7 November 2026

**Status:** 585/585 technical QA lulus, **BELUM final ready akademik**. Semua fail dan kawalan baharu hanya di cabang `staging/matematik-ba-evidence-20261107`; tiada merge atau perubahan produksi.

## 1. Punca kegagalan sementara CI v48 ditangani
Run GitHub `42323276578` gagal kerana ujian mewajibkan pautan kadar BNM pada **T4-L055 SP 3.5.1** (mengenal mata wang), sedangkan rujukan BNM hanya perlu pada **SP3.5.2** (kadar nilai RM1). Kegagalan merupakan **kesilapan ujian**, bukannya bukti latihan v48 salah. Ujian diperbaiki pada commit `604fa30afd2ddc3555b13a0f0bed155293be1b21` dan GitHub Actions telah **SUCCESS** run `42323400677`. Kandungan RPH tidak diubah akibat pembetulan ujian.

## 2. BNM [=1 Malaysian ringgit] disahkan pada sumber primer
Paparan Bank Negara Malaysia: `https://www.bnm.gov.my/latest-rates` membezakan kadar bagi *Foreign Currency Units* dengan nilai **[=1 Malaysian ringgit]** dalam kurungan. Untuk pelajaran berkaitan **SP Tahun 3 4.6.2 dan Tahun 4 3.5.2**, guru mesti membaca nilai dalam kurungan [ ] dan menyatakan nilai mata wang asing bagi **RM1**, bukan RM bagi satu unit mata wang asing. Tarikh kadar mesti sama dengan tarikh PdP atau tarikh sumber rujukan yang dinyatakan. **Tiada kadar November 2026 disalin untuk tahun 2027**.

v49 memperincikan arahan bacaan kurungan pada tiga RPH: `T3-L060`, `T4-L056`, `T4-L057`.

## 3. Tempoh 20 minit yang berganda dibuang daripada isi aktiviti
Enam RPH Tahun 4 `T4-L109` hingga `T4-L113` dan `T4-L116` mempunyai catatan `(20 minit)` tambahan dalam teks Aktiviti 1/2; tempoh itu sudah ada di label aktiviti. **Tujuh** catatan berganda dibuang daripada enam RPH, tanpa menukar data/kaedah pengiraan, langkah atau masa asal.

Bukti tepat setiap seksyen sebelum/selepas: `audits/matematik_v49_10_section_fixes_20261107.csv`. Jumlah **10** suntingan pada **9** RPH; 576 RPH lain byte-identical. Setiap suntingan diterapkan pada Markdown, Word, PDF; kedua-dua PDF gabungan Tahun 3 dan Tahun 4 dijana semula.

## 4. Artifak dan QA
- ZIP: `CIKGULAJU_MATEMATIK_v49_585_RPH_KADAR_RM1_DAN_MASA_STAGING.zip`
- Saiz: **48,774,109 bait**; SHA-256: `fcc3e7fe07ed6eb9cb0abdff1ef3bd1765c7050a6d8e036b81abd199ae4835b0`.
- Sumber v48 SHA-256: `a19841be74474f819496f694faebcd75e617864bfac9c48c4b3e841ec0393b4b`.
- 585 DOCX, 585 PDF A4 satu halaman, 585 Markdown dan 5 PDF gabungan. ZIP CRC `testzip()==None`. Teks PDF terkini untuk 9 RPH dipastikan tidak melebihi tepi halaman; sampel visual Tahun 4 L056 dan L110 diluluskan semakan susun atur.
- Rujukan BA Tahun 2–3: **234 lesson** kekal; 46 set induksi konkrit daripada v47 dan 4 pembetulan mata wang berdasarkan DSKP daripada v48 kekal.
- `rph_standalone/matematik/staging_preview_v49.py` hanya opt-in, hash ZIP terkunci, terasing daripada produksi dan gagal tertutup.
- `tests/test_matematik_ba_v49_preview_20261107.py`, `tests/test_matematik_ba_v49_ten_edits_20261107.py` menyemak gate dan perubahan, termasuk `final_ready=false`.

## 5. Baki sebelum final ready
- Semakan latihan spesifik dan pentaksiran PBD terhadap setiap SP bagi **585 lesson** belum mempunyai signoff akademik per item. Sampel BA yang telah disemak tidak meluluskan semuanya secara automatik.
- **34** pasangan sesi pengembangan Tahun 4 memerlukan semakan akademik latihan buku yang nyata; hanya kod DSKP dan aktiviti berbeza telah disahkan. Buku Teks Tahun 4 dalam Drive bersaiz 306 MB, melebihi had muat turun connector 256 MB; belum dinilai sepenuhnya.
- Kalendar 2027 mengikut negeri/Kumpulan A-B dan penjajaran PdP/RPT perlu ujian.
- **Telegram/Web staging sebenar** terhadap DB kanonik dan hak akses pengguna belum diuji (ujian loader ialah synthetic/offline).
- Pakej ZIP v49 tersedia sebagai artifak perbualan; Library hampir penuh, jadi hanya matriks QA kecil disimpan di Library. **Tiada penghapusan/overwrite arkib lama**.

**Release gate:** `TECHNICAL_QA=PASS`; `GITHUB_CI=RECHECK_AFTER_METADATA_FIX`; `ACADEMIC_ITEM_SIGNOFF=0`; `STAGING_E2E=NOT_RUN`; `FINAL_READY=false`.

## Pengesahan ZIP sebenar selepas metadata diselaraskan
Pakej v49 awal menghasilkan schema `academic_final_ready=false` tetapi tiada `final_ready=false` yang diperlukan oleh loader. Isu dikesan melalui ujian local dengan fail ZIP sebenar (ujian sintetik CI sahaja tidak mengesannya). Metadata `AUDIT/V49_RELEASE_GATE.json` ditambah `final_ready=false` tanpa mengubah mana-mana daripada 585 Word/PDF/Markdown; hash baharu dikunci ke dalam loader v49.

**12/12 ujian pratonton terhadap ZIP sebenar LULUS** selepas pembetulan: 585 PDF tersedia, Word dan PDF boleh dipilih mengikut lesson, pengesahan SHA, pengguna berbayar/admin, callback lama, penolakan tanpa akses, input palsu dan kegagalan penghantaran, serta perlindungan DB/kuota. Ini **ujian setempat/mock**, bukan ujian Telegram/Web sebenar. Release gate akademik masih HOLD.
