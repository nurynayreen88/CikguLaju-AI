"use strict";
// Pure source-contract QA. No browser, Telegram, user account, Supabase, or credit write.
const assert=require("node:assert/strict");
const fs=require("node:fs");
const vm=require("node:vm");

const daily=fs.readFileSync("web_v1_static_preview/rph-today.js","utf8");
const html=fs.readFileSync("web_v1_static_preview/index.html","utf8");
const declarations=daily.slice(daily.indexOf(" const TYPES="), daily.indexOf(" function create("));
const start=daily.indexOf(" function readyMaterialLink(");
const end=daily.indexOf(" async function inspectOne(",start);
assert.ok(start>0&&end>start&&declarations.includes("student_book"),"Expected sourced material guard");
const sandbox={};
vm.runInNewContext(declarations+daily.slice(start,end)+"\nthis.readyMaterialLink=readyMaterialLink;",sandbox);
const allowed=sandbox.readyMaterialLink;

const studentBook={
 type:"student_book",title:"English Year 4 Student Book - printed pages 121",
 url:"/api/web/rph/english-student-book?year=4&subject=ENGLISH&unit=Unit+5&lesson=EN4-L043"
};
assert.equal(allowed(studentBook,4,"ENGLISH"),true,
 "English Y4 Student Book should be listed once the verified partner API returns it");
assert.equal(allowed(studentBook,3,"ENGLISH"),false,"Year 3 must not inherit Year 4 Student Book");
assert.equal(allowed(studentBook,4,"MATH"),false,"Other subjects must not inherit Student Book");
assert.equal(allowed({...studentBook,url:"https://example.com/book.pdf"},4,"ENGLISH"),false);
assert.equal(allowed({...studentBook,url:"/api/web/rph/english-workbook?year=4"},4,"ENGLISH"),false);
assert.equal(allowed({...studentBook,title:""},4,"ENGLISH"),false);
assert.equal(allowed({...studentBook,type:"textbook"},4,"ENGLISH"),false,
 "Never display generic unverified textbook links");

const workbook={type:"workbook",title:"English Year 4 Workbook",
 url:"/api/web/rph/english-workbook?year=4&lesson=EN4-L002"};
const worksheet={type:"worksheet",title:"Lembaran Kerja Tambahan Lesson 004",
 url:"/api/web/rph/english-worksheet?year=4&subject=ENGLISH&unit=Unit+1&lesson=e-4-004"};
assert.equal(allowed(worksheet,4,"ENGLISH"),true,
 "Registered teacher-created English Y4 worksheet must be selectable by exact Lesson");
assert.equal(allowed(worksheet,3,"ENGLISH"),false,
 "Year 3 must not inherit Year 4 worksheets");
assert.equal(allowed(worksheet,4,"MATH"),false,
 "Other subjects must never inherit English worksheets");
assert.equal(allowed({...worksheet,url:"https://external.example/worksheet.pdf"},4,"ENGLISH"),false);
assert.equal(allowed({...worksheet,url:"/api/web/rph/english-workbook?year=4"},4,"ENGLISH"),false);

assert.equal(allowed(workbook,4,"ENGLISH"),true,
 "Existing independent verified Workbook bridge must not regress");
const audio={type:"audio",title:"Original Music audio",
 url:"https://drive.google.com/file/d/1234567890ABCD/view?usp=drivesdk"};
assert.equal(allowed(audio,4,"MUZIK"),true,
 "Existing source-hosted Music audio must not regress");
assert.equal(allowed({...audio,url:"https://example.com/audio.mp3"},4,"MUZIK"),false);

assert.match(html,/<title>CikguLaju AI — Pusat Sehenti Guru Sekolah Rendah<\/title>/);
assert.match(html,/>Tahun 1–6 · PdP &amp; Bahan<\/span>/);
assert.match(html,/data-web-view="today" aria-controls="view-today"/,
 "Existing PdP Hari Ini route stays intact");
assert.match(html,/id="today-generate-all"/,"Original batch-selection flow remains");
assert.match(html,/id="rph-word"/,"Existing Word generation remains");
assert.match(html,/id="rph-pdf"/,"Existing PDF generation remains");
assert.match(html,/id="web-admin-tab"[^>]*hidden/,"Admin menu remains private");
assert.match(html,/id="web-referral-tab"[^>]*hidden/,"Referral menu remains private");
assert.ok(!/data-web-view="(pbd|worksheet|exam|bbm)"/.test(html),
 "Do not introduce modules without available backend sources");
assert.match(html,/cikgulaju-logo\.svg/,"Original school product logo retained");

console.log("PRIMARY_PDP_HUB: PASS (Y4 Student Book guarded, existing sources preserved, no empty menus)");
