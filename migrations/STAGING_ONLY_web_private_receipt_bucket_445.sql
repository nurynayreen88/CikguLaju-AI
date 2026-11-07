-- STAGING ONLY. Create a private receipt bucket in the DEDICATED staging
-- Supabase instance. Never apply this script to production.
BEGIN;
INSERT INTO storage.buckets(id,name,public,file_size_limit,allowed_mime_types)
VALUES ('web-receipts-staging','web-receipts-staging',false,4194304,
        array['application/pdf','image/png','image/jpeg','image/webp'])
ON CONFLICT (id) DO NOTHING;

-- Fail if a pre-existing bucket has been made public or misconfigured.
DO $body$
BEGIN
  IF NOT EXISTS (
    SELECT 1 FROM storage.buckets
    WHERE id='web-receipts-staging' AND public IS FALSE
      AND file_size_limit = 4194304
  ) THEN
    RAISE EXCEPTION 'Receipt bucket must be private and limited to 4MB';
  END IF;
END;
$body$;
-- No anon/authenticated grants. Only the staging service_role can upload
-- or download via backend, after verifying a Web user or admin.
COMMIT;
