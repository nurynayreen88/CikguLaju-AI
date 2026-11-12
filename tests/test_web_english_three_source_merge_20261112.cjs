"use strict";
/* Exact source-bound book links. Never inherit another Lesson via a metadata URL. */
const assert=require("node:assert/strict");
const fs=require("node:fs");
const vm=require("node:vm");
const html=fs.readFileSync("web_v1_static_preview/index.html","utf8");
const begin=html.indexOf("function verifiedBookMaterialLink(");
const end=html.indexOf("function verifiedWorksheetMaterialLink(",begin);
assert.ok(begin>0&&end>begin,"Dedicated verified book guard is required");
const ctx={URLSearchParams};
vm.runInNewContext(html.slice(begin,end)+"\nthis.allow=verifiedBookMaterialLink;",ctx);
const allow=ctx.allow;
const base={year:"4",subject:"ENGLISH",unit:"Get Smart Plus Unit 1",lesson:"EN4-L004"};
function row(type,sel=base){
 const route=type==="workbook"?"english-workbook":"english-student-book";
 return {type,title:"Verified English source",url:"/api/web/rph/"+route+"?"+
 new URLSearchParams(sel).toString()};
}
for(const type of ["workbook","student_book"]){
 const item=row(type);
 assert.equal(allow(item,"4","ENGLISH",base.unit,base.lesson),true,type);
 assert.equal(allow(item,"3","ENGLISH",base.unit,base.lesson),false);
 assert.equal(allow(item,"4","BM",base.unit,base.lesson),false);
 assert.equal(allow(item,"4","ENGLISH","Wrong Unit",base.lesson),false);
 assert.equal(allow(item,"4","ENGLISH",base.unit,"EN4-L005"),false);
 assert.equal(allow({...item,title:""},"4","ENGLISH",base.unit,base.lesson),false);
 assert.equal(allow({...item,url:"https://evil.example/x"},"4","ENGLISH",base.unit,base.lesson),false);
 assert.equal(allow({...item,url:item.url+"&lesson=EN4-L005"},"4","ENGLISH",base.unit,base.lesson),false);
 assert.equal(allow({...item,url:item.url+"&admin=1"},"4","ENGLISH",base.unit,base.lesson),false);
 assert.equal(allow({...item,url:item.url.replace("english-","other-")},"4","ENGLISH",base.unit,base.lesson),false);
}
const y2={year:"2",subject:"ENGLISH",unit:"Unit 2",lesson:"e-2-003"};
assert.equal(allow(row("workbook",y2),"2","ENGLISH","Unit 2","e-2-003"),true);
assert.equal(allow(row("student_book",y2),"2","ENGLISH","Unit 2","e-2-003"),false);
assert.match(html,/const ownStudentBook=item.type==="student_book"&&verifiedBookMaterialLink/);
assert.match(html,/if\(!ownWorkbook&&!ownStudentBook&&!ownWorksheet&&!ownWorksheetWord&&!externalMusic\)continue;/);
assert.match(html,/<details id="worksheet-submenu" hidden/);
console.log("THREE_SOURCE_BOOK_LINKS: PASS (all source identities exact; worksheet menu retained)");
