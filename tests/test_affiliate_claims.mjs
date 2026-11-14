import {readFileSync} from "node:fs";
import assert from "node:assert/strict";
import {PGlite} from "@electric-sql/pglite";

const db = new PGlite();
const sql = (query, params) => db.query(query, params);
const result = async query => (await sql(query)).rows[0].result;
await db.exec(`CREATE ROLE anon; CREATE ROLE authenticated; CREATE ROLE service_role BYPASSRLS;
  CREATE TABLE public.cikgulaju_users(telegram_user_id bigint PRIMARY KEY,
      created_at timestamptz NOT NULL DEFAULT now(), first_name text, username text);
  CREATE TABLE public.pioneer_entitlements(telegram_user_id bigint, payment_reference text, entitlement text,
      approved_at timestamptz, approved_by bigint, revoked_at timestamptz);
  CREATE TABLE public.subscription_payments(telegram_user_id bigint, payment_reference text,
      amount_rm numeric, status text, created_at timestamptz);
  GRANT SELECT, INSERT ON public.cikgulaju_users TO service_role;
  GRANT SELECT, UPDATE ON public.pioneer_entitlements, public.subscription_payments TO service_role;
  INSERT INTO public.cikgulaju_users(telegram_user_id) VALUES (10),(11),(12),(13),(14),(15);
  UPDATE public.cikgulaju_users SET first_name='Affiliate Ujian', username='affiliate_ujian' WHERE telegram_user_id=10;`);
for (const name of ["migrations/20261104_private_referral_points.sql", "supabase/migrations/20261113223611_affiliate_claims.sql"]) {
  await db.exec(readFileSync(name,"utf8"));
}
assert.equal((await result("SELECT affiliate_save_wallet(10,'0123456789') result")).error, "closed");
await sql("UPDATE referral_reward_settings SET affiliate_claims_enabled=true, reward_percent=10 WHERE id=1");
await sql("SET ROLE service_role");
assert.equal((await result("SELECT affiliate_save_wallet(10,'0123456789') result")).saved, true);
const member = (await sql("SELECT referral_code FROM referral_members WHERE referrer_user_id=10")).rows[0];
await result("SELECT affiliate_save_wallet(10,'01123456789') result");
assert.equal((await sql("SELECT referral_code FROM referral_members WHERE referrer_user_id=10")).rows[0].referral_code, member.referral_code);
assert.equal((await result("SELECT affiliate_save_wallet(99,'0123456789') result")).error, "invalid");
await sql("UPDATE referral_members SET enabled=false WHERE referrer_user_id=10");
assert.equal((await result("SELECT affiliate_save_wallet(10,'0123456789') result")).error, "disabled");
await sql("UPDATE referral_members SET enabled=true WHERE referrer_user_id=10");
await sql(`INSERT INTO referral_point_events(referrer_user_id,referred_user_id,payment_kind,payment_reference,points_delta)
  VALUES (10,11,'pioneer','P1',14.50), (10,12,'subscription','S2',11.00);`);
assert.deepEqual((await sql("SELECT DISTINCT reward_percent FROM referral_point_events")).rows, [{reward_percent:"10.00"}]);
const legacyKey = "00000000-0000-4000-8000-000000000099";
const legacy = await result(`SELECT affiliate_submit_claim(10,10,'01123456789','${legacyKey}') result`);
await sql("RESET ROLE");
await db.exec(readFileSync("supabase/migrations/20261113225317_affiliate_duitnow_account.sql", "utf8"));
await db.exec(readFileSync("supabase/migrations/20261113231252_affiliate_point_balances.sql", "utf8"));
await sql("UPDATE referral_members SET enabled=false WHERE referrer_user_id=10");
await db.exec(readFileSync("supabase/migrations/20261114033218_auto_referral_members_existing_new_v2.sql", "utf8"));
assert.equal((await sql("SELECT enabled FROM referral_members WHERE referrer_user_id=10")).rows[0].enabled, false);
await sql("UPDATE referral_members SET enabled=true WHERE referrer_user_id=10");

await sql("SET ROLE service_role");
const autoMember = async uid => (await sql(
  "SELECT referral_code FROM referral_members WHERE referrer_user_id=$1", [uid])).rows[0];
assert.match((await autoMember(15)).referral_code, /^[a-f0-9]{32}$/);
await sql("INSERT INTO cikgulaju_users (telegram_user_id) VALUES (16)");
const newCode = (await autoMember(16)).referral_code;
assert.match(newCode, /^[a-f0-9]{32}$/);
assert.notEqual(newCode, (await autoMember(15)).referral_code);
assert.equal((await result("SELECT affiliate_overview(16) result")).account_number, null);
assert.equal((await autoMember(10)).referral_code, member.referral_code);
assert.equal((await result("SELECT affiliate_overview(10) result")).account_number, null);
assert.equal((await result("SELECT affiliate_save_wallet(10,'0123456789') result")).error, "account_required");
assert.equal((await result(`SELECT affiliate_submit_claim(10,10,'01123456789','${legacyKey}') result`)).error,"account_required");
assert.equal((await result(`SELECT affiliate_review_claim('${legacy.id}',21,'processing',NULL,NULL,NULL,NULL) result`)).error,"account_required");
assert.equal((await result(`SELECT affiliate_review_claim('${legacy.id}',21,'rejected',NULL,'Tuntut semula dengan nombor akaun',NULL,NULL) result`)).status,"rejected");
assert.equal((await result("SELECT affiliate_save_account(10,'0123456789') result")).error, "invalid");
assert.equal((await result("SELECT affiliate_save_account(10,'001234567890') result")).saved, true);
assert.equal((await result("SELECT affiliate_save_account(13,'000000000013') result")).saved, true);
await sql("UPDATE referral_members SET enabled=false WHERE referrer_user_id=13");
const directory = await result("SELECT affiliate_admin_members(0,25) result");
const noClaims = directory.items.find(row => row.user_id === "13");
assert.deepEqual(noClaims, {user_id:"13", enabled:false, first_name:null, username:null,
  registered_count:0, payment_count:0, balance:0, earned:0, paid:0, reserved:0, available:0});
assert.equal(directory.items.find(row => row.user_id === "10").first_name,"Affiliate Ujian");
assert.equal((await result("SELECT affiliate_admin_members(0,1) result")).more,true);
assert.equal((await result("SELECT affiliate_admin_members(1,1) result")).items.length,1);
const balances = async (balance, reserved, paid, available) => {
  const self = await result("SELECT affiliate_overview(10) result");
  const {items} = await result("SELECT affiliate_admin_members(0,25) result");
  const admin = items.find(row => row.user_id === "10");
  for (const row of [self, admin]) {
    assert.deepEqual([row.balance, row.reserved, row.paid, Number(row.available)], [balance,reserved,paid,available]);
  }
  assert.equal("account_number" in admin,false);
};
await balances(25.5,0,0,25.5);
assert.equal((await result("SELECT affiliate_overview(10) result")).account_number,"001234567890");
assert.equal((await sql("SELECT phone FROM affiliate_wallets WHERE user_id=10")).rows[0].phone,null);
assert.equal((await sql("SELECT referral_code FROM referral_members WHERE referrer_user_id=10")).rows[0].referral_code, member.referral_code);
const key1="00000000-0000-4000-8000-000000000001";
const key2="00000000-0000-4000-8000-000000000002";
const key3="00000000-0000-4000-8000-000000000003";
const key4="00000000-0000-4000-8000-000000000004";
const submit=(points,key,account="001234567890")=>result(`SELECT affiliate_submit_account_claim(10,${points},'${account}','${key}') result`);
assert.equal((await submit(9.99,key1)).error,"invalid");
assert.equal((await submit(10,key1,"002345678901")).error,"wallet_changed");
const first = await submit(10,key1);
assert.equal(first.status,"pending");
await balances(25.5,10,0,15.5);
assert.equal((await submit(10,key1)).id,first.id);
assert.equal((await submit(10.01,key1)).error,"request_conflict");
const requests = await Promise.all([submit(10,key2),submit(10,key3)]);
assert.deepEqual(requests.map(row=>row.error || row.status).sort(),["balance","pending"]);
const second = requests.find(row=>row.status==="pending");
assert.equal((await result("SELECT affiliate_overview(10) result")).available,"5.50");
await result("SELECT affiliate_save_account(10,'002345678901') result");
assert.equal((await sql(`SELECT account_number_snapshot FROM affiliate_claims WHERE id='${first.id}'`)).rows[0].account_number_snapshot,"001234567890");
const review=(id,admin,action,reference="NULL",reason="NULL",mime="NULL",proof="NULL")=>result(
  `SELECT affiliate_review_claim('${id}',${admin},'${action}',${reference},${reason},${mime},${proof}) result`);
assert.equal((await review(first.id,21,"paid")).error,"status");
assert.equal((await review(first.id,21,"processing")).status,"processing");
await balances(25.5,20,0,5.5);
assert.equal((await review(first.id,22,"processing")).error,"status");
assert.equal((await review(first.id,22,"paid")).error,"status");
assert.equal((await review(first.id,21,"paid","'TNG-001'")).error,"invalid");
assert.equal((await review(first.id,21,"paid","'TNG-001'","NULL","'application/pdf'","decode('255044462d','hex')")).status,"paid");
assert.equal((await review(first.id,21,"paid","'TNG-001'")).status,"paid");
await balances(15.5,10,10,5.5);
assert.equal((await sql(`SELECT count(*)::int AS n FROM affiliate_claim_events WHERE claim_id='${first.id}'`)).rows[0].n,3);
assert.equal((await review(second.id,21,"processing")).status,"processing");
assert.equal((await review(second.id,21,"paid","'TNG-001'","NULL","'application/pdf'","decode('255044462d','hex')")).error,"reference_used");
assert.equal((await review(second.id,21,"rejected","NULL","'Nombor tidak aktif'")).status,"rejected");
await balances(15.5,0,10,15.5);
assert.equal((await result("SELECT affiliate_overview(10) result")).available,"15.50");
assert.equal((await submit(10,key4,"002345678901")).status,"pending");
await sql("RESET ROLE");
await sql("INSERT INTO pioneer_entitlements VALUES (11,'P1','PIONEER_LIFETIME',now(),21,NULL)");
await sql("UPDATE pioneer_entitlements SET revoked_at=now() WHERE telegram_user_id=11");
assert.equal((await result("SELECT affiliate_overview(10) result")).available,"0");
await balances(1,10,10,0);
assert.equal((await sql("SELECT count(*)::int AS n FROM affiliate_point_reversals")).rows[0].n,1);
await sql("SET ROLE authenticated");
await assert.rejects(sql("SELECT phone FROM affiliate_wallets"),/permission denied/);
await assert.rejects(sql("SELECT affiliate_overview(10)"),/permission denied/);
await assert.rejects(sql("SELECT affiliate_admin_members(0,25)"),/permission denied/);
await assert.rejects(sql("SELECT affiliate_point_summary(10)"),/permission denied/);
await assert.rejects(sql("SELECT content FROM affiliate_claim_proofs"),/permission denied/);
await db.close();
console.log("Affiliate SQL integration passed: enrollment, minimum, replay, reservation, admin ownership, proof, rejection, reversal, grants.");
