# Pendidikan Islam 2027 — staging QA V2 (5 November 2026)

**STAGING ONLY — DRAF, BELUM READY.** Tiada deploy, main merge atau Telegram production.

## Fail yang telah dibina
- 696 RPH Word Tahun 2–6: T2=112, T3=147, T4=151, T5=143, T6=143.
- 5 RPT Word sumber QA v4 dan **5 PDF RPT A4 landskap dengan muka depan** (T2:41 halaman; T3:52; T4:53; T5:50; T6:51).
- 696 baris audit individu dan 35 baris semakan risiko dengan alasan per Lesson.
- Pakej berasingan: `CIKGULAJU_PI_2027_T2_T6_696_RPH_5_RPT_V2_STAGING_20261105.zip`, SHA-256 `f5913d65f561cfaa26f4e6db24f3e849b847ce71048136aeed62fe4f1e444733`. **Pakej ZIP tidak dimasukkan ke repository atau runtime; disimpan sebagai artefak staging.**

## Pembetulan tepat
- Tahun 5 L134, objektif ketiga bernombor 2 secara tersilap; dibetulkan menjadi 3, tanpa mengubah ayat Jawi atau kod SP.
- Word L134 dirender dan diperiksa visual satu halaman A4.
- 695 RPH Word lain tidak berubah pada aras SHA-256 berbanding checkpoint sebelumnya.

## Klasifikasi risiko yang tetap
- `CALON_UJIAN_GURU_DRAF` 661; `SEMAKAN_KEUTAMAAN` 29; `TAHAN_SEMAKAN_KANDUNGAN` 6.
- Enam tahanan: T2 L035; T6 L006, L014, L018, L060 dan L117.
- L060 ialah RPH pengganti amali solat ketika sakit; perlu pengesahan guru bahawa ia boleh digunakan untuk slot asal dalam RPT.
- L117 membuang az-Zumar 1–5 yang keliru berada bawah Juz 29 dalam sumber; semakan guru masih perlu.
- 23 RPH Tahun 6 masih memerlukan semakan Jawi/buku teks/tema, dengan satu L087 bidang Hadis sebagai semakan terpisah.
- Jurang tasmi' tidak dilengkapkan dengan tekaan. Bertindih ayat al-Baqarah 224 dan julat tasmi' Tahun 6 kekal sebagai isu sumber.

## Ujian terhad dan larangan
- ZIP integrity, 696/696 lesson ID unik, 695 fail tidak berubah, satu fail objektif diperbetul sahaja.
- Lima PDF mempunyai muka depan, saiz landskap A4, tiada halaman teks kosong; dua halaman contoh Tahun 2 disemak visual.
- Ini **bukan** ujian glyph menyeluruh atau semantik DSKP/buku teks terhadap semua 696 dokumen.
- Jangan aktifkan standalone PI pada Telegram atau Web, jangan menukar source DB, tidak sentuh `app.py`, transaksi, akaun, atau modul lain.

## Sebelum mengisytiharkan READY
Sahkan 35 Lesson khusus, nilai 696 kandungan dengan rubrik pedagogi sebenar, periksa semua page visual Word/PDF, sahkan takwim negeri dan laluan penghantaran staging. Bilangan fail dan lulus XML bukan kelulusan kandungan.
