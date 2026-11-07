-- Disposable PostgreSQL only. All test accounts, link rows, jobs, object
-- metadata and ledgers are rolled back. No real user payment/data change.
BEGIN;
-- Supabase's real service_role bypasses RLS. The disposable CI role created
-- by tests/sql/web_google_payment_fixture.sql lacks this flag by default.
-- Transaction rollback restores the disposable role afterward.
ALTER ROLE service_role BYPASSRLS;
-- Fake Storage fixture grants needed for local role simulation only.
GRANT USAGE ON SCHEMA storage TO service_role;
GRANT SELECT ON storage.objects TO service_role;
DO $setup$
DECLARE a uuid;
BEGIN
 a := public.ensure_google_web_account(
   'a1e7c000-0000-4000-8000-000000000045'::uuid,'Paid staging test');
 PERFORM public.link_verified_telegram_web_account_staging(a,123456789);
 PERFORM public.prepare_web_rph_bundle_staging(
   a,'a1e7c000-0000-4000-8000-000000000041'::uuid,repeat('a',64));
 PERFORM public.prepare_web_rph_bundle_staging(
   a,'a1e7c000-0000-4000-8000-000000000042'::uuid,repeat('b',64));
 INSERT INTO storage.objects(bucket_id,name) VALUES
 ('web-rph-bundles-staging',a::text||'/a1e7c000-0000-4000-8000-000000000041.docx'),
 ('web-rph-bundles-staging',a::text||'/a1e7c000-0000-4000-8000-000000000041.pdf'),
 ('web-rph-bundles-staging',a::text||'/a1e7c000-0000-4000-8000-000000000042.docx'),
 ('web-rph-bundles-staging',a::text||'/a1e7c000-0000-4000-8000-000000000042.pdf');
END;
$setup$;

DO $privileges$
BEGIN
 IF has_function_privilege('anon',
    'public.complete_web_rph_bundle_prod_paid_staging(uuid,uuid,text,bigint)','EXECUTE')
 OR has_function_privilege('authenticated',
    'public.complete_web_rph_bundle_prod_paid_staging(uuid,uuid,text,bigint)','EXECUTE')
 OR NOT has_function_privilege('service_role',
    'public.complete_web_rph_bundle_prod_paid_staging(uuid,uuid,text,bigint)','EXECUTE')
 THEN RAISE EXCEPTION 'Production paid RPH function grants are not private'; END IF;
 -- postgres must be barred from invoking function as non-service_role.
 BEGIN
  PERFORM public.complete_web_rph_bundle_prod_paid_staging(
    (SELECT account_id FROM public.web_account_identities
      WHERE provider='google' AND subject='a1e7c000-0000-4000-8000-000000000045'),
    'a1e7c000-0000-4000-8000-000000000041'::uuid,repeat('c',64),123456789);
  RAISE EXCEPTION 'Non-service role bypassed paid completion';
 EXCEPTION WHEN raise_exception THEN
   IF SQLERRM <> 'Private paid completion requires service role'
   THEN RAISE; END IF;
 END;
END;
$privileges$;

SET LOCAL ROLE service_role;
DO $verify$
DECLARE
 a uuid;
 r jsonb;
 n integer;
BEGIN
 SELECT account_id INTO a FROM public.web_account_identities
 WHERE provider='google' AND subject='a1e7c000-0000-4000-8000-000000000045';
 IF a IS NULL THEN RAISE EXCEPTION 'Paid fixture identity missing'; END IF;
 BEGIN
  PERFORM public.complete_web_rph_bundle_prod_paid_staging(
     a,'a1e7c000-0000-4000-8000-000000000041'::uuid,repeat('c',64),999999999);
  RAISE EXCEPTION 'Wrong Telegram ID accepted';
 EXCEPTION WHEN raise_exception THEN
   IF SQLERRM NOT LIKE 'Linked staging account balance or identity%'
   THEN RAISE; END IF;
 END;

 r := public.complete_web_rph_bundle_prod_paid_staging(
   a,'a1e7c000-0000-4000-8000-000000000041'::uuid,repeat('c',64),123456789);
 IF r->>'status'<>'ready' OR r->>'access_mode'<>'paid'
    OR (r->>'remaining')::int<>10
 THEN RAISE EXCEPTION 'Paid completion not ready at full unchanged quota: %',r; END IF;
 r := public.complete_web_rph_bundle_prod_paid_staging(
   a,'a1e7c000-0000-4000-8000-000000000041'::uuid,repeat('c',64),123456789);
 IF r->>'status'<>'ready' OR (r->>'replayed')::boolean IS DISTINCT FROM true
 THEN RAISE EXCEPTION 'Paid completion replay unsafe: %',r; END IF;
 BEGIN
  PERFORM public.complete_web_rph_bundle_prod_paid_staging(
    a,'a1e7c000-0000-4000-8000-000000000041'::uuid,repeat('d',64),123456789);
  RAISE EXCEPTION 'Manifest collision accepted';
 EXCEPTION WHEN raise_exception THEN
   IF SQLERRM<>'Previously ready job manifest mismatch' THEN RAISE; END IF;
 END;

 r := public.complete_web_rph_bundle_prod_paid_staging(
   a,'a1e7c000-0000-4000-8000-000000000042'::uuid,repeat('e',64),123456789);
 IF (r->>'remaining')::int<>10 THEN RAISE EXCEPTION 'Paid repeat debited quota'; END IF;
 SELECT google_trial_remaining INTO n FROM public.web_accounts WHERE id=a;
 IF n<>10 THEN RAISE EXCEPTION 'Verified lifetime job consumed a trial credit'; END IF;
 SELECT count(*) INTO n FROM public.web_rph_delivery_ledger
 WHERE account_id=a AND access_mode='paid';
 IF n<>2 THEN RAISE EXCEPTION 'Paid ledger not exactly once per bundle'; END IF;
 RAISE NOTICE 'PASS: two paid bundles, zero trial credit debit, idempotence, and account binding';
END;
$verify$;
ROLLBACK;
