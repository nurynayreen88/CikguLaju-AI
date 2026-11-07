# Google Login CikguLaju — Panduan Pemilik (7 November 2026)

## Sudah disahkan
- Render staging: https://cikgulaju-google-payments-staging.onrender.com
- GitHub: PR #447, cabang `feature/web-google-auth-staging-445` (draft, belum merge).
- Staging service mempunyai ciri kawalan keselamatan: Google login **OFF**, pembayaran sebenar **OFF**, RPH pengguna **OFF** sehingga pengesahan.
- Laman staging menampilkan penjelasan dalam BM apabila OAuth OFF, bukan butang login rosak.
- Senarai organisasi Supabase yang disambung memperlihatkan **ContentLajuAI**; belum ada projek Supabase staging CikguLaju khusus. Pangkalan data produksi CikguLaju tidak akan dijadikan ujian.
- Kod sudah merangkumi PKCE, tiket sesi terasing, akaun UUID, 10 kredit awal di data staging, muat naik resit ujian, pengesahan admin berasingan. Ini bukan bukti Google OAuth melalui pelayar sudah diuji.

## Bahagian yang memerlukan tindakan pemilik (tidak boleh dibuat tanpa akses/kelulusan)
1. **Pilih organisasi Supabase dan sahkan kos.** Sebelum mencipta projek `CikguLaju-Google-Staging`, pastikan organisasi yang dipilih dan kos yang dikemukakan diluluskan. Projek ini hanya untuk staging; jangan gunakan projek CikguLaju produksi, Klippo, atau cabang yang menggandakan rekod pengguna sebenar.
2. **Google Auth Platform.** Di https://console.cloud.google.com/auth/clients cipta OAuth Client, jenis **Web application**. Semasa menyediakan skrin persetujuan, gunakan skop minimum `openid`, `userinfo.email`, `userinfo.profile`. Pastikan akaun ujian dibenarkan jika aplikasi dalam mod Testing.
3. **URI Google Cloud** (selepas mendapat ref projek baru): 
   - Authorized JavaScript origin: `https://cikgulaju-google-payments-staging.onrender.com`
   - Authorized redirect URI: `https://<NEW_STAGING_SUPABASE_REF>.supabase.co/auth/v1/callback` (semak URL tepat pada panel Supabase Google Provider).
   - Jangan letak `/api/auth/google/callback` dalam senarai redirect URI Google Cloud; ia untuk tahap Supabase → Web.
4. **Supabase staging → Authentication → Providers → Google.** Tampal Client ID dan **Client Secret di dashboard Supabase**; jangan kongsi rahsia dalam chat/GitHub. Auth URL Configuration → Add Redirect URL: `https://cikgulaju-google-payments-staging.onrender.com/api/auth/google/callback`.
5. **Render staging → Environment.** Masukkan ref staging, publishable key, backend service key, rahsia sesi Web berasingan dan origin/host yang tepat seperti `docs/google-payments-staging-runbook-445.md`. Nilai production ref hanya digunakan untuk menghalang sambungan ke DB produksi. `CIKGULAJU_GOOGLE_AUTH_STAGING_ENABLED` kekal `0` sehingga migrasi DB staging & ujian konfigurasi selesai.
6. **Migrasi staging sahaja.** Jalankan empat fail SQL `STAGING_ONLY_...445.sql` yang sudah diuji pada PostgreSQL sementara di CI, selepas semakan RLS, dan sahkan 10 kredit awal serta pengasingan resit. Pembayaran sebenar mesti kekal OFF.
7. Aktifkan Google staging, deploy **staging sahaja**, dan cuba login dalam pelayar telefon serta PC. Uji login pertama, login semula, logout dan penolakan sesi palsu. Pembayaran/resit hanya gunakan bahan simulasi.
8. Reka pemindahan ke produksi **selepas** lulus ujian: satu identiti akaun bersama bagi Google+Telegram (link hanya selepas bukti kedua-duanya), baki 10 janaan yang sama, langganan, referral, pembayaran dan kuota Rakan Pembangun global. Jangan padankan Google dengan Telegram melalui emel atau nama.

## Ralat yang mudah dikesan
- Render `/healthz` = 200 hanya bermaksud Flask berjalan; ia tidak bermaksud OAuth berjaya.
- `/readyz` = 503 bermaksud **konfigurasi login Google belum lengkap**, bukan server mati.
- `/readyz` menyediakan `google_login_configured` dan `admin_review_configured` secara berasingan kerana guru Google tidak perlu Telegram.
- `/google-staging-login` = 503 halaman penjelasan sebelum OAuth staging diaktifkan.
- Tidak boleh minta pengguna membayar TNG sebenar di laman staging.

Sumber docs:
https://supabase.com/docs/guides/auth/social-login/auth-google
https://supabase.com/docs/guides/auth/redirect-urls
