"use strict";
/* Upcoming modules are deliberately read-only, unlike real Lesson-bound content. */
const assert=require("node:assert/strict");
const fs=require("node:fs");
const source=fs.readFileSync("web_v1_static_preview/index.html","utf8");
const nav=source.split('<nav class="sidebar-menu"')[1]?.split("</nav>")[0];
assert.ok(nav,"Original navigation must remain in place");
assert.match(nav,/<button type="button" class="sidebar-tab" data-web-view="upcoming" aria-controls="view-upcoming">/);
assert.match(nav,/Bahan Akan Datang.*?Akan Datang/);
const view=source.match(/<section id="view-upcoming" class="app-view"[^>]*hidden>([\s\S]*?)<\/section>/);
assert.ok(view,"Read-only upcoming panel must start hidden");
assert.match(view[1],/belum boleh dimuat turun/);
assert.match(view[1],/Tiada tarikh pelancaran yang dijanjikan/);
assert.match(view[1],/RPH Hari Ini, Sediakan RPH, RPH Aktiviti Khas dan RPT 2027/);
assert.match(view[1],/RM20 sekali bayar/);
assert.match(view[1],/akses seumur hidup/);
assert.match(view[1],/termasuk modul baharu apabila dilancarkan/);
assert.match(view[1],/tanpa bayaran tambahan/);
assert.match(view[1],/pilih menu <strong>Rakan Pembangun<\/strong>/);
for(const item of ["Bank Lembaran Kerja Tahun 1–6","BBM &amp; Aktiviti",
                    "Latihan UASA","Rekod PBD","KP2027 Tahun 1"]){
 assert.ok(view[1].includes(item),"A planned module is missing: "+item);
}
assert.equal((view[1].match(/<span>Akan Datang<\/span>/g)||[]).length,5,"Every planned module needs explicit status");
assert.doesNotMatch(view[1],/<(?:a|button|form|input|select)\b/i,
 "No fake download, purchase, form or clickable action for unapproved modules");
assert.doesNotMatch(nav,/data-web-view="worksheet"|data-web-view="pbd"|data-web-view="uasa"|data-web-view="bbm"/,
 "Do not create fake working routes");
assert.match(source,/\["upcoming","view-upcoming"\]/,"Navigation must actually switch to the panel");
for(const name of ["today","rph","special","rpt","account","payment","feedback","admin","guide"])
 assert.ok(source.includes('["'+name+'","view-'+name+'"]'),"Existing navigation removed: "+name);
assert.match(nav,/id="web-admin-tab"[^>]*hidden/,"Private admin must stay hidden");
assert.match(nav,/id="web-referral-tab"[^>]*hidden/,"Private referral must stay hidden");
assert.equal(/href=|onclick=/.test(view[1]) || view[1].includes("fetch("), false,
 "Coming Soon is only information, not an active download route");
assert.match(source,/id="show-materials"/,"Original RPH options remain intact");
console.log("UPCOMING_MATERIALS_MENU: PASS (roadmap is visible, inactive sources locked, original navigation intact)");
