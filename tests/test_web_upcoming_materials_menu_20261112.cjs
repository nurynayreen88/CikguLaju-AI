"use strict";
/* Upcoming features appear at their own sidebar positions, not inside a
 * generic Bahan Akan Datang menu. All planned pages are read-only previews. */
const assert=require("node:assert/strict");
const fs=require("node:fs");
const vm=require("node:vm");
const source=fs.readFileSync("web_v1_static_preview/index.html","utf8");
const nav=source.split('<nav class="sidebar-menu"')[1]?.split("</nav>")[0];
assert.ok(nav,"Original navigation remains");
assert.doesNotMatch(nav,/Bahan Akan Datang|data-web-view="upcoming"/,
 "No separate upcoming bucket in the sidebar");
assert.doesNotMatch(source,/id="view-upcoming"/,
 "The old bucket must not remain as a hidden orphan");

const features=[
 ["worksheet","Lembaran Kerja"],
 ["bbm","BBM &amp; Aktiviti"],
 ["uasa","Latihan UASA"],
 ["kp2027","KP2027 • Tahun 1"],
];
const locations=features.map(([id,label])=>{
 const re=new RegExp('<button type="button" class="sidebar-tab sidebar-tab--planned" data-web-view="'+id+'" aria-controls="view-'+id+'">([^<]*|[\\s\\S]*?)<\\/button>');
 const match=nav.match(re);
 assert.ok(match,"Separate sidebar tab missing: "+id);
 assert.ok(match[0].includes(label), "Wrong label for "+id);
 assert.match(match[0],/<span class="sidebar-coming-status">Akan Datang<\/span>/,
  "Every planned feature must display its own Coming Soon badge");
 const view=source.match(new RegExp('<section id="view-'+id+'" class="app-view"[^>]*hidden>([\\s\\S]*?)<\\/section>'));
 assert.ok(view,"Information view must start hidden for "+id);
 assert.match(view[1],/Akan Datang/);
 assert.doesNotMatch(view[1],/<(?:a|button|form|input|select)\b/i,
  "No fake downloads or generation controls inside "+id);
 assert.doesNotMatch(view[1],/href=|onclick=|fetch\(/,
  "No external routes or quota actions inside "+id);
 assert.match(source,new RegExp('\\["'+id+'","view-'+id+'"\\]'),
  "Navigation map must open "+id);
 return {id,label,index:nav.indexOf('data-web-view="'+id+'"'),content:view[1]};
});
const pos=id=>nav.indexOf('data-web-view="'+id+'"');
assert.ok(pos("rph")<pos("worksheet") && pos("worksheet")<pos("bbm") &&
 pos("bbm")<pos("uasa") && pos("uasa")<pos("pbd") &&
 pos("pbd")<pos("special"),"Teaching-material features should follow Sediakan RPH");
assert.ok(pos("rpt")<pos("kp2027") && pos("kp2027")<pos("payment"),
 "KP2027 should sit next to RPT 2027, not in a separate bucket");

const worksheet=locations.find(x=>x.id==="worksheet").content;
assert.match(worksheet,/Enam contoh susun atur A4/);
assert.match(worksheet,/bukan enam modul yang sudah siap/);
assert.match(worksheet,/belum boleh dimuat turun/);
assert.match(worksheet,/tiada tarikh pelancaran yang dijanjikan/);
const samples=["english-004","english-079","english-089","english-090","math-y1","science-y1"];
const ids=[...worksheet.matchAll(/<details class="upcoming-sample" data-upcoming-sample="([^"]+)">/g)].map(x=>x[1]);
assert.deepEqual(ids,samples,"All six source-backed A4 visual previews remain in Lembaran Kerja");
const images=[...worksheet.matchAll(/<img loading="lazy" decoding="async" width="794" height="1123" alt="([^"]+)" src="([^"]+)">/g)];
assert.equal(images.length,6);
for(const [,alt,uri] of images){
 assert.match(alt,/Gambar lembaran A4/);
 assert.ok(uri.startsWith("data:image/svg+xml;charset=utf-8,"));
 const svg=decodeURIComponent(uri.slice("data:image/svg+xml;charset=utf-8,".length));
 assert.match(svg,/<svg[^>]+viewBox="0 0 794 1123"/);
 assert.match(svg,/PRATONTON SUSUN ATUR/);
 assert.doesNotMatch(svg,/Answer key|Teacher assessment|SECRET_|jawapan guru/i);
}
for(const text of [
 "She is from Malaysia. She is __________.",
 "Which character made an important choice?",
 "One checked fact: ____________________",
 "What is the event?",
 "Kumpulan manakah lebih banyak?",
 "Lihat pensel kamu. Apakah warna pensel itu?"
])assert.ok(worksheet.includes(text),"Missing pupil-only sample content: "+text);
assert.match(worksheet,/Belum ada pautan PDF\/Word/);
assert.equal((worksheet.match(/<summary>/g)||[]).length,6);
assert.doesNotMatch(worksheet,/Answer key|Teacher assessment|Kunci Jawapan|jawapan guru:/i);

for(const feature of locations){
 assert.match(feature.content,/RM20 sekali bayar/);
 assert.match(feature.content,/akses seumur hidup/);
 assert.match(feature.content,/tanpa bayaran tambahan/);
 assert.match(feature.content,/pilih menu <strong>Rakan Pembangun<\/strong>/);
}
assert.match(nav, /class="sidebar-tab" data-web-view="pbd"/);
assert.match(source, /id="pbd-save-roster"/);
assert.match(locations.find(x=>x.id==="kp2027").content,/RPT 2027/);
for(const name of ["today","rph","special","rpt","account","payment","referral","feedback","admin","guide"]){
 assert.ok(source.includes('["'+name+'","view-'+name+'"]'),
 "Existing navigation changed unexpectedly: "+name);
}
assert.match(nav,/id="web-admin-tab"[^>]*hidden/);
assert.match(nav,/id="web-referral-tab"[^>]*hidden/);
assert.match(source,/id="show-materials"/,"Existing RPH options remain");
assert.match(source,/function showWebView\(name\)/);
const scripts=[...source.matchAll(/<script>([\s\S]*?)<\/script>/g)];
assert.equal(scripts.length,1,"Keep one native inline JS script");
new vm.Script(scripts[0][1],"web JS must parse");
console.log("WEB_PLANNED_MENUS: PASS (four planned sidebar slots, badges, six visual previews, no fake downloads)");
