-- CikguLaju first Rakan Pembangun batch: 200 confirmed active members.
-- Non-destructive: never delete/modify any entitlement, payment or user row.
-- Preserve the existing advisory lock (20261026, 500) for concurrent approvals
-- and all existing function ownership, SECURITY settings and EXECUTE grants.
-- Updates only the two quota thresholds and their returned remaining counts.
DO $rakan_cap_200$
DECLARE
  active_count integer;
  approval_definition text;
  reactivation_definition text;
BEGIN
  SELECT count(*)::integer INTO active_count
  FROM public.pioneer_entitlements
  WHERE entitlement = 'PIONEER_LIFETIME' AND revoked_at IS NULL;

  IF active_count > 200 THEN
    RAISE EXCEPTION 'Existing Rakan Pembangun active member count exceeds new cap; cannot lower automatically';
  END IF;

  SELECT pg_get_functiondef('public.approve_pioneer_early_bird(bigint,text,bigint)'::regprocedure)
    INTO approval_definition;
  SELECT pg_get_functiondef('public.reactivate_pioneer_after_revocation(bigint,text,bigint,bigint)'::regprocedure)
    INTO reactivation_definition;

  IF approval_definition IS NULL OR reactivation_definition IS NULL
      OR position('pg_advisory_xact_lock(20261026, 500)' IN approval_definition) = 0
      OR position('pg_advisory_xact_lock(20261026, 500)' IN reactivation_definition) = 0 THEN
    RAISE EXCEPTION 'Existing atomic approval/reactivation implementations differ from audited baseline';
  END IF;

  IF position('IF n >= 500 THEN' IN approval_definition) > 0
      AND position('''remaining'',499-n' IN approval_definition) > 0 THEN
    approval_definition := replace(approval_definition,'IF n >= 500 THEN','IF n >= 200 THEN');
    approval_definition := replace(approval_definition,'''remaining'',499-n','''remaining'',199-n');
    EXECUTE approval_definition;
  ELSIF position('IF n >= 200 THEN' IN approval_definition) = 0
      OR position('''remaining'',199-n' IN approval_definition) = 0 THEN
    RAISE EXCEPTION 'Unexpected approval cap implementation: no changes were made';
  END IF;

  IF position('if v_active_count >= 500 then' IN reactivation_definition) > 0
      AND position('''remaining'', 499 - v_active_count' IN reactivation_definition) > 0 THEN
    reactivation_definition := replace(reactivation_definition,
       'if v_active_count >= 500 then','if v_active_count >= 200 then');
    reactivation_definition := replace(reactivation_definition,
       '''remaining'', 499 - v_active_count','''remaining'', 199 - v_active_count');
    EXECUTE reactivation_definition;
  ELSIF position('if v_active_count >= 200 then' IN reactivation_definition) = 0
      OR position('''remaining'', 199 - v_active_count' IN reactivation_definition) = 0 THEN
    RAISE EXCEPTION 'Unexpected reactivation cap implementation: no changes were made';
  END IF;
END
$rakan_cap_200$;
