"use strict";
/* Menu-level QA: no separate main tab, only verified exact-Lesson worksheets. */
const assert=require("node:assert/strict");
const fs=require("node:fs");
const vm=require("node:vm");
const html=fs.readFileSync("web_v1_static_preview/index.html","utf8");

assert.match(html,/data-web-view="rph" aria-controls="view-rph"[^>]*>.*Sediakan Bahan PdP<\/button>/,
 "Keep existing RPH view/flow, rename only the teacher-facing menu");
assert.doesNotMatch(html,/data-web-view="worksheet"/,
 "Do not create a separate unsupported main worksheet menu");
assert.match(html,/<details id="worksheet-submenu" hidden[^>]*>/,
 "Worksheet submenu starts hidden");
assert.match(html,/<summary>📄 Lembaran Kerja/);
assert.match(html,/<ul id="worksheet-materials-list"/);
assert.match(html,/worksheetMaterialList\.replaceChildren\(\);\s*worksheetSubmenu\.hidden=true;/,
 "Stale worksheet results must be removed before every fetch");
assert.match(html,/worksheetSubmenu\.hidden=false;/,
 "Reveal only after real verified worksheet formats were appended");
assert.match(html,/if\(worksheetMaterialList\.children\.length\)/,
 "No empty submenu may be visible");
assert.match(html,/const target=\(ownWorksheet\|\|ownWorksheetWord\)\?worksheetMaterialList:list;/,
 "Only matched worksheet items move into the submenu; RPH and Workbook stay elsewhere");
assert.match(html,/id="materials-panel"/,
 "Preserve the native existing panel used by RPH Hari Ini too");
assert.match(html,/id="rph-pdf"/);
assert.match(html,/id="rph-word"/);

const start=html.indexOf("function verifiedWorksheetMaterialLink(");
const end=html.indexOf("function materialRow(",start);
assert.ok(start>0&&end>start,"Required pure source guard must exist");
const sandbox={URLSearchParams};
vm.runInNewContext(html.slice(start,end)+
  "\nthis.verifiedWorksheetMaterialLink=verifiedWorksheetMaterialLink;",sandbox);
const allow=sandbox.verifiedWorksheetMaterialLink;
const unit="Get Smart Plus Unit 1",token="EN4-L004";
function fixture(type,year="4",subject="ENGLISH",punit=unit,lesson=token){
 const route=type==="worksheet"?"/api/web/rph/english-worksheet":
  "/api/web/rph/english-worksheet-word";
 return {type,title:"Lembaran Kerja English Year 4 Lesson 004",
  url:route+"?"+new URLSearchParams({year,subject,unit:punit,lesson}).toString()};
}
for(const type of ["worksheet","worksheet_word"]){
 const row=fixture(type);
 assert.equal(allow(row,"4","ENGLISH",unit,token),true,
  "Exact authenticated route for chosen Year/Unit/Lesson must be visible");
 assert.equal(allow(row,"3","ENGLISH",unit,token),false,
  "Year 1-3 cannot inherit Year 4 worksheets");
 assert.equal(allow(row,"4","BM",unit,token),false);
 assert.equal(allow(row,"4","ENGLISH","Other Unit",token),false);
 assert.equal(allow(row,"4","ENGLISH",unit,"EN4-L005"),false);
 assert.equal(allow({...row,title:""},4,"ENGLISH",unit,token),false);
 assert.equal(allow({...row,url:"https://example.net/worksheet.pdf"},4,"ENGLISH",unit,token),false);
 assert.equal(allow({...row,url:row.url+"&admin=1"},4,"ENGLISH",unit,token),false);
 assert.equal(allow({...row,url:row.url+"&lesson=EN4-L060"},4,"ENGLISH",unit,token),false);
 assert.equal(allow({...row,url:row.url.replace("EN4-L004","EN4-L005")},
  4,"ENGLISH",unit,token),false);
 const invalidRoute=type==="worksheet"?"english-worksheet?":"english-worksheet-word?";
 assert.equal(allow({...row,url:row.url.replace(invalidRoute,"english-workbook?")},
  4,"ENGLISH",unit,token),false);
}
assert.equal(allow({type:"worksheet",title:"Dummy Mathematics Year 1",
 url:"/api/web/rph/english-worksheet?year=1&subject=MATH&unit=A&lesson=1"},
 "1","MATH","A","1"),false,"Year 1 unapproved dummy must not render");
assert.equal(allow(fixture("worksheet"),"4","ENGLISH",unit,token),true);
console.log("WORKSHEET_SUBMENU: PASS (conditional PDF/Word submenu, exact identity, no dummy or main tab)");
