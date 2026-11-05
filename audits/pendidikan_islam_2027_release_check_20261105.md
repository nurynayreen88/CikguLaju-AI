# Pendidikan Islam — pemeriksaan pra-penerbitan, 2026-11-05

**KEPUTUSAN: NO-GO. JANGAN MERGE / DEPLOY KE TELEGRAM ATAU WEB.**

Pengguna membenarkan penerbitan **hanya jika** bahan telah lulus pemeriksaan. Syarat tersebut belum dipenuhi. Ini arahan bersyarat, bukannya arahan mengatasi release gate.

## Pemeriksaan GitHub yang disahkan
- `main` semasa pada commit `3da8d49a83005bebb2715411fadebe30a9df791c`.
- Cabang `staging/pendidikan-islam-2027-t2-t6-qa-20261105` telah berpisah daripada `main`: 10 commit di hadapan dan **17 commit di belakang**.
- Perbezaan cabang hanya **10 fail audit/ujian**. Tiada 696 RPH Word atau lima PDF RPT V3 sebagai fail deployable dalam cabang.
- Lima PDF RPT yang sedia ada di `main` terletak di `rpt_2027/pendidikan_islam/` bersama `telegram_downloads.py`; adapter sedia ada menyampaikan PDF setempat dengan label `Cadangan untuk semakan guru`. Itu **tidak membuktikan** RPH V3 tersedia melalui Telegram.
- Tidak terdapat status CI atau workflow run untuk commit staging `d52f378faac7f7486691ab5b494bc4614dc68eda` melalui semakan sambungan.
- Pakej V3 sumber ialah `/CikguLaju/Pendidikan_Islam_2027_STAGING/CIKGULAJU_PI_2027_T2_T6_AUDIT_V3_PEMBETULAN_TERKAWAL_STAGING_20261105.zip` di Library, **bukan** di repository.
- Lapan pengecualian cakupan tasmi' kekal direkod dan pengesahan semantik baris demi baris terhadap semua 696 RPH belum lengkap.

## Keperluan sebelum boleh merge
1. Sahkan semantik dan liputan tasmi' serta putuskan lapan pengecualian tanpa mengada-adakan ayat/standard.
2. Masukkan fail deployable V3 secara terkawal ke cabang staging, bukan menimpa fail lama secara rawak. Sahkan SHA dan jumlah Lesson.
3. Rebase/compose perubahan terhadap `main` terkini untuk mengelak overwrite 17 commit kerja lain.
4. Uji download/render dan kawalan akses di runtime staging dengan data sebenar, termasuk regresi subjek lain.
5. Lulus ujian CI dan release gate. Hanya selepas itu pertimbangkan merge terhad.

**Operasi kini:** Audit sahaja. Tiada `main` merge, tiada produksi deploy, tiada perubahan `app.py`, akaun atau database pengguna.