# CikguLaju — Rekod Pengguna Kekal di Supabase (2026-11-04)

## Matlamat
Deployment Render tidak boleh memadam status pengguna, pendaftaran, kelas, jadual, bayaran, mata referral atau keputusan semakan admin. **Jangan reset / overwrite data.**

## Sumber data disemak
| Rekod | Sumber semasa / selepas aktif | Status |
|---|---|---|
| Identiti Telegram, nama | `cikgulaju_users` + `teacher_profiles` | Persistent; nama Telegram diselaraskan |
| Profil, negeri, kelas, bilangan murid, jadual waktu | `teacher_profiles.class_profiles` dan `class_names` | Persistent (kod sedia ada) |
| Percubaan 10 RPH, baki, ledger | `cikgulaju_users.trial_remaining`, `trial_ledger` | Persistent (kod sedia ada) |
| Status langganan, bayaran langganan | `subscriptions`, `subscription_payments` | Persistent (kod sedia ada) |
| Rakan Pembangun yang diluluskan | `pioneer_entitlements` | Persistent (kod sedia ada) |
| Referral, rakan didaftar, mata dibayar | `referral_members`, `referral_signups`, `referral_point_events` | Persistent (kod sedia ada) |
| RPH berjaya/gagal & kemajuan | `rph_generation_history`, `rph_progress` | Persistent apabila write Supabase berjaya |
| Permohonan baru, pending, resit, semakan & sejarah keputusan | `bot_payment_requests` | **Baharu, diaktifkan melalui flag** |
| Komen, cadangan, status dibaca/selesai & laporan PDF | `bot_user_feedback` | **Baharu, diaktifkan melalui flag** |

## Migrasi & keselamatan
- `migrations/20261104_durable_telegram_payments_feedback.sql` — jadual tambahan, index dan RPC kiraan.
- `migrations/20261104_durable_telegram_payment_proof_refs.sql` — rujukan fail resit Telegram (bukan foto mentah), supaya ID fail dan mesej tidak hanya tinggal dalam RAM/SQLite.
- Kedua-dua jadual baharu mempunyai RLS ON. `anon` dan `authenticated` tidak boleh SELECT, INSERT, UPDATE atau DELETE. Hanya backend `service_role`.
- Nombor payment request dijana oleh PostgreSQL; tidak lagi bermula semula apabila Render deploy.
- Fail resit **tidak dimuat naik sebagai bytes ke Supabase Storage**. ID fail Telegram disimpan supaya backend boleh mencarinya semula selagi Telegram membenarkan akses.
- Tiada perubahan kepada jadual lama / credits / entitlements / DSKP / DB kurikulum.

## Pengaktifan
1. Apply kedua-dua migrasi tambahan di Supabase dan sahkan RLS / role.
2. Pastikan CI menjalankan `test_supabase_user_records.py`, `test_private_referral_points.py`, `test_private_referral_admin.py`. Test fail-closed, admin-only, cancel sendiri, duplicate pending, identiti, proof pointer dan restart.
3. Merge PR selepas CI; kod **OFF** secara lalai.
4. Set `CIKGULAJU_SUPABASE_USER_RECORDS=1` di Render selepas semak sambungan backend dan rekod sedia ada.
5. Periksa startup `DURABLE USER RECORDS: SUPABASE PAYMENT QUEUE ENABLED` dan `... FEEDBACK ENABLED`, kemudian semak butang Admin Panel → Pending dan Komen.
6. Ujian satu permohonan tanpa bayaran sebenar: butang, nota pending dan pembacaan selepas restart; jangan lakukan pengesahan palsu. Semak dengan bayaran sebenar yang admin sudah sahkan sebelum uji ganjaran.

## Had pemulihan penting
- Rekod *lama* yang hanya pernah berada dalam SQLite runtime sebelum migrasi ini mungkin sudah tiada akibat deploy terdahulu. **Jangan cipta semula jumlah bayaran, status approved atau rujukan palsu.** Rekonsiliasi mesti menggunakan bukti bank/TNG, resit Telegram atau audit yang benar-benar wujud.
- Identiti pengguna yang sudah berada dalam Supabase tidak dipadam / ditimpa. Migrasi tidak membuat backfill andaian.
- Sesi butang/borang yang belum selesai (`state[cid]` in-memory), sejarah resit sumbangan Beta dalam jadual SQLite lama, dan fail Word/PDF yang belum dihantar **belum dipindahkan secara penuh**. Sesi sementara perlu dibina semula apabila restart; ini tidak menukar status bayaran yang telah disahkan.
- Mengaktifkan sumber pending baharu tidak boleh dianggap sebagai pengesahan bahawa semua pending SQLite lama telah dipindahkan. Urusan rekonsiliasi lama perlu dibuat satu per satu, tanpa meminta pelanggan bayar semula.

## Prinsip operasi
- Kalau Supabase tidak tersedia, **jangan** beralih ke local SQLite/angka 0 secara senyap untuk permohonan bayaran. Papar ralat boleh dicuba semula.
- Keputusan approved perlu hanya oleh admin, batal pending oleh pemilik sahaja; jangan dedahkan data orang lain.
- Buat perubahan **additive** dan boleh diaudit. Jangan padam snapshot atau data asal.
