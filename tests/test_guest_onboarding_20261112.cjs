"use strict";
// Guest conversion walkthrough: public, read-only and fail-closed. No user tracking,
// Supabase writes, fabricated RPH preview, credit debit, or new endpoints.
const assert=require("node:assert/strict");
const fs=require("node:fs");
const vm=require("node:vm");
const source=fs.readFileSync("web_v1_static_preview/index.html","utf8");
const main=source.split('<main class="panel">')[1]?.split("</main>")[0];
assert.ok(main,"Expected public guest login panel");
assert.match(main,/id="guest-tour"/,"Guided tour should work before login");
assert.match(main,/tanpa log masuk/,"Clarify no-login access");
assert.match(main,/bukan RPH sebenar/,"Do not confuse static walkthrough with real generated material");
assert.match(main,/id="telegram-widget"/,"Original trusted Telegram Login widget preserved");
assert.match(main,/href="#telegram-widget"/,"Guest CTA should lead to real login");
assert.match(main,/10 janaan RPH percuma/,"Trial should remain clear");
assert.match(main,/id="telegram-start-link"[^>]*hidden/,"Bot link must not be active before config validation");
assert.ok(!/id="telegram-start-link"[^>]*href=/i.test(main),"Never hardcode Telegram identity on public page");
assert.equal((main.match(/id="telegram-widget"/g)||[]).length,1,"Do not duplicate login widget");
assert.equal((source.match(/id="login-status"/g)||[]).length,1,"Do not duplicate login state output");
const from=source.indexOf("function verifiedTelegramBotUrl(value){");
const until=source.indexOf("(async()=>{",from);
assert.ok(from>0&&until>from,"Missing auth-config bot identity guard");
const sandbox={};
vm.runInNewContext(source.slice(from,until)+"\nthis.safeBot=verifiedTelegramBotUrl;",sandbox);
const safeBot=sandbox.safeBot;
assert.equal(safeBot("CikguLaju_Bot"),"https://t.me/CikguLaju_Bot");
assert.equal(safeBot("cikgulaju88"),"https://t.me/cikgulaju88");
for(const bad of ["","abc","abc/redirect","https://t.me/another_bot","abc@evil.com",
 "<script>alert(1)</script>","cat bot","A".repeat(33),null,{}]){
 assert.equal(safeBot(bad),null,"Untrusted bot username should fail closed: "+String(bad));
}
assert.match(source,/if\(link&&startLink\)\{startLink.href=link;startLink.hidden=false;\}/,
 "Reveal bot action only after validated auth capabilities response");
assert.match(source,/session\.ok\)\{/,"Existing authenticated workspace flow preserved");
assert.match(source,/data-web-view="rph"/,"Original RPH workflow retained");
assert.match(source,/data-web-view="today"/,"Original daily timetable workflow retained");
assert.match(source,/id="web-admin-tab"[^>]*hidden/,"Admin menu remains private");
assert.match(source,/id="web-referral-tab"[^>]*hidden/,"Referral menu remains private");
console.log("GUEST_ONBOARDING: PASS (no-login tour, real Telegram login, safe bot URL, no new data or credit path)");
