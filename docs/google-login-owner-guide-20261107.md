# Google Login CikguLaju — Panduan Pemilik (7 November 2026)

## Sudah disahkan
- Render staging: https://cikgulaju-google-payments-staging.onrender.com
- GitHub: PR #447, cabang `feature/web-google-auth-staging-445` (draft, belum merge).
- Staging service mempunyai ciri kawalan keselamatan: Google login **OFF**, pembayaran sebenar **OFF**, RPH pengguna **OFF** sehingga pengesahan.
- Laman staging menampilkan penjelasan dalam BM apabila OAuth OFF, bukan butang login rosak.
- **SELESAI:** Projek `CikguLaju-Google-Staging` diwujudkan dalam organisasi `ContentLajuAI`, Singapura, pada kos yang disahkan **$0 sebulan**. Project ref: `eqrcjlnvcytkgazptbor`. Dashboard: https://supabase.com/dashboard/project/eqrcjlnvcytkgazptbor
- **SELESAI:** Empat migrasi staging (identiti, pembayaran, bucket resit, RPC review) berjaya. Semua empat jadual diasingkan dengan RLS, tanpa akses baca `anon`/`authenticated`. Bucket resit private, had 4 MiB. Ujian pendaftaran berulang sahkan satu ID dengan 10 kredit; data ujian dibersihkan.
- **SELESAI:** Tetapan bukan rahsia Supabase staging + publishable key + session secret rawak baharu sudah disimpan dalam Render staging. Suis Google masih OFF. Produksi tidak diubah.
- Kod sudah merangkumi PKCE, tiket sesi terasing, akaun UUID, 10 kredit awal di data staging, muat naik resit ujian, pengesahan admin berasingan. Ini bukan bukti Google OAuth melalui pelayar sudah diuji.

## Bahagian yang memerlukan tindakan pemilik (tidak boleh dibuat tanpa akses/kelulusan)
1. **SELESAI — Supabase staging.** Projek berasingan dalam organisasi ContentLajuAI sudah diwujudkan dan kosnya $0 sebulan. Jangan gunakan DB produksi untuk ujian.
2. **Google Auth Platform.** Di https://console.cloud.google.com/auth/clients cipta OAuth Client, jenis **Web application**. Semasa menyediakan skrin persetujuan, gunakan skop minimum `openid`, `userinfo.email`, `userinfo.profile`. Pastikan akaun ujian dibenarkan jika aplikasi dalam mod Testing.
3. **URI Google Cloud** (selepas mendapat ref projek baru): 
   - Authorized JavaScript origin: `https://cikgulaju-google-payments-staging.onrender.com`
   - Authorized redirect URI: `https://eqrcjlnvcytkgazptbor.supabase.co/auth/v1/callback` (semak URL tepat pada panel Supabase Google Provider).
   - Jangan letak `/api/auth/google/callback` dalam senarai redirect URI Google Cloud; ia untuk tahap Supabase → Web.
4. **Supabase staging → Authentication → Providers → Google.** Buka https://supabase.com/dashboard/project/eqrcjlnvcytkgazptbor/auth/providers dan tampal Client ID serta **Client Secret secara peribadi di dashboard Supabase**; jangan kongsi rahsia dalam chat/GitHub. Auth URL Configuration → Add Redirect URL: `https://cikgulaju-google-payments-staging.onrender.com/api/auth/google/callback`.
5. **Render staging → Environment.** Ref staging, URL, publishable key, sesi rahsia unik dan origin/host **telah disediakan**. **Baki:** Masukkan backend `CIKGULAJU_GOOGLE_STAGING_SUPABASE_SERVICE_ROLE_KEY` daripada *projek staging sahaja* ke tetapan persekitaran **Render staging** (bukan chat/GitHub), kerana konektor tidak boleh mengakses private key. Pastikan `CIKGULAJU_GOOGLE_AUTH_STAGING_ENABLED=0` sehingga Google Provider/redirect disemak.
6. **SELESAI — migrasi staging sahaja.** Empat fail SQL berjaya dijalankan pada pangkalan data ujian khusus, dan semakan RLS, kredit awal 10 serta pengasingan resit lulus. Pembayaran sebenar mesti kekal OFF.
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
