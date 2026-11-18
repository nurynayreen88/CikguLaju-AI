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
assert.doesNotMatch(source,/id="view-kp2027"|data-web-view="kp2027"/);
assert.match(source,/<select id="curriculum">.*<option value="kssr">KSSR \(SK\)<\/option><option value="sjkc">KSSR \(SJKC\)<\/option><option value="sjkt">KSSR \(SJKT\) — Dalam Penyediaan<\/option><option value="kp2027">KP27 \(KP Baharu\)<\/option><option value="dlp">DLP<\/option><\/select>/);
assert.match(source,/<select id="year" hidden disabled>/);
assert.match(source,/<select id="subject" hidden disabled>/);
assert.match(source,/year===1\?"Tahun 1 \(KP Baharu\)"/);

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
const code=scripts[0][1];
const listeners={};
function mockSelect(name){
 return {value:"",options:[],addEventListener(event,fn){listeners[name+"."+event]=fn;}};
}
const curriculum=mockSelect("curriculum"),year=mockSelect("year"),subject=mockSelect("subject"),unit=mockSelect("unit");
const lesson=mockSelect("lesson"),theme=mockSelect("theme"),topic=mockSelect("topic"),component=mockSelect("component");
const catalogueCalls=[];
const panel={hidden:true}, heading={textContent:""};
const makeNode=()=>({textContent:"",children:[],append(...items){this.children.push(...items);},replaceChildren(){this.children=[];}});
const content=makeNode();
const dlpReviewData=JSON.parse(source.match(/<script id="dlp-review-data" type="application\/json">([\s\S]*?)<\/script>/)[1]);
assert.deepEqual(Object.values(dlpReviewData).map(groups=>groups.map(group=>group.lessons.length)),[[7,1,5,7,6,6,7,7,11,6],[12,21,8,11,6,10,6,4]]);
const variantRpt={hidden:true,dataset:{}}, materials={hidden:true,disabled:true};
let checkedRph=0;
const variants=[
 {code:"science_dlp",label:"Science (DLP)",rph_code:"SCIENCE_DLP",curriculum:"dlp",rpt_years:[2,3,4,5,6]},
 {code:"mathematics_dlp",label:"Mathematics (DLP)",rph_code:"MATH_DLP",curriculum:"dlp",rpt_years:[2,3,4,5,6]},
 {code:"matematik_sjkc",label:"Matematik (SJKC)",curriculum:"sjkc",rpt_years:[2]},
 ...[
  ["bahasa_iban","Bahasa Iban"],["bahasa_kadazandusun","Bahasa Kadazandusun"],
  ["bahasa_semai","Bahasa Semai"],["bahasa_cina_sk","Bahasa Cina (SK)"],["bahasa_tamil_sk","Bahasa Tamil (SK)"]
 ].map(([code,label])=>({code,label,curriculum:"kssr"})),
];
const ctx={
 curriculum,year,subject,unit,lesson,theme,topic,component,catalogStatus:{textContent:""},
 dlpPreviewPanel:panel,dlpReviewHeading:heading,dlpReviewContent:content,dlpReviewData,
 window:{cikgulajuSubjectVariants:variants},rphSubjectPicker:{sync(){}},
 document:{createElement:makeNode,createTextNode:text=>({textContent:text}),getElementById:id=>id==="show-materials"?materials:variantRpt},
 resetSelect(el,label){el.value="";el.options=[{value:"",label}];el.disabled=true;},
 fillSelect(el,items,label){ctx.resetSelect(el,label);el.options.push(...items);el.disabled=!items.length;},
 resetCurriculumChoices(){ctx.showDlpReview(null);ctx.resetSelect(unit,"");ctx.resetSelect(lesson,"");unit.hidden=lesson.hidden=variantRpt.hidden=true;delete variantRpt.dataset.subject;},
 setSubjectNavigationLabels(){},
 resetMaterials(){},resetRphPreview(){},showRphAction(){},displayBookReference(){},
 updateSelectionHelp(text){ctx.help=text;},
 async loadOptions(kind){catalogueCalls.push(kind);return [{value:"MATH",label:"Matematik"}];},
 showStep(el,visible){el.hidden=!visible;}, subjectNavLabel(){return "Unit";},
 async fillForSelection(el,kind,extra){
  catalogueCalls.push(kind,extra.subject);
  if(extra.subject==="MATH_DLP")ctx.fillSelect(el,[{value:"01",label:"Unit 1 Whole Numbers and Operations"}],"Pilih Unit");
  if(extra.subject==="SCIENCE_DLP")ctx.fillSelect(el,[{value:"01",label:"Unit 1 Scientific Skills"}],"Pilih Unit");
 },
 async loadFinalLesson(kind,extra){
  catalogueCalls.push(kind,extra.subject,extra.unit);
  const science=extra.subject==="SCIENCE_DLP";
  ctx.fillSelect(lesson,[{value:`DLP-${science?"SCI":"MATH"}-Y${year.value}-L01`,
    label:science?"Lesson 01 • Observe":"Lesson 01 • Whole Numbers"}],"Pilih Lesson");
 },
 async checkRphAvailability(){checkedRph++;},
};
vm.runInNewContext(code.slice(code.indexOf("const subjectVariants="),code.indexOf("async function loadOptions("))
 +"\n"+code.slice(code.indexOf('curriculum.addEventListener("change"'),code.indexOf('const MATERIAL_CATEGORIES'))
 +"\nthis.showDlpReview=showDlpReview;",ctx);
(async()=>{
 listeners["curriculum.change"]();
 assert.equal(year.hidden,true);
 assert.equal(subject.hidden,true);
 curriculum.value="kp2027";
 listeners["curriculum.change"]();
 assert.deepEqual(year.options.map(x=>x.label),["Pilih Tahun","Tahun 1 (KP Baharu)"]);
 year.value="1";
 await listeners["year.change"]();
 assert.equal(subject.disabled,true);
 assert.equal(subject.hidden,true);
 assert.match(ctx.help,/KP Baharu.*Akan Datang/i);
 assert.deepEqual(catalogueCalls,[]);
 curriculum.value="sjkc";
 listeners["curriculum.change"]();
 for(const yearNumber of ["2","3"]){
  year.value=yearNumber;
  await listeners["year.change"]();
  assert.equal(subject.options[1].label,"Matematik (SJKC) — RPH Dalam Penyediaan");
  subject.value="matematik_sjkc";
  await listeners["subject.change"]();
  assert.equal(variantRpt.hidden,true);
  assert.equal(variantRpt.dataset.subject,undefined);
  assert.equal(unit.hidden,true);
  assert.equal(lesson.hidden,true);
  assert.match(ctx.help,/dalam penyediaan/i);
 }
 curriculum.value="sjkt";
 listeners["curriculum.change"]();
 assert.equal(year.hidden,true);
 assert.equal(subject.hidden,true);
 assert.equal(variantRpt.hidden,true);
 assert.match(ctx.help,/RPH SJKT masih dalam penyediaan/);
 assert.deepEqual(catalogueCalls,[]);
 curriculum.value="dlp";
 listeners["curriculum.change"]();
 assert.deepEqual(year.options.map(x=>x.label),[
  "Pilih Tahun","Tahun 1 (KP Baharu) — Dalam Penyediaan","Tahun 2 — Untuk Semakan Guru",
  "Tahun 3 — Dalam Penyediaan","Tahun 4 — Dalam Penyediaan","Tahun 5","Tahun 6"
 ]);
 year.value="2";
 await listeners["year.change"]();
 assert.deepEqual(subject.options.map(x=>x.value),["","SCIENCE_DLP","MATH_DLP"]);
 for(const [subjectCode,groups] of Object.entries(dlpReviewData)){
  let lessonNumber=0;
  subject.value=subjectCode;
  await listeners["subject.change"]();
  assert.equal(variantRpt.hidden,false);
  assert.equal(panel.hidden,true);
  assert.deepEqual(unit.options.map(x=>x.value),["",...groups.map(group=>group.id)]);
  for(const group of groups){
   unit.value=group.id;
   await listeners["unit.change"]();
   assert.equal(panel.hidden,true);
   assert.equal(lesson.options.length,group.lessons.length+1);
   for(const item of group.lessons){
    assert.equal(item.number,++lessonNumber);
    const label = "Lesson "+String(lessonNumber).padStart(2,"0")+" — "+item.title;
    assert.equal(lesson.options.find(option=>option.value===item.id).label,label);
    lesson.value=item.id;
    listeners["lesson.change"]();
    assert.equal(heading.textContent,label);
    assert.equal(panel.hidden,false);
    const allowedMinutes=subjectCode==="MATH_DLP"?[60]:[30,60];
    assert.ok(allowedMinutes.includes(item.minutes));
    assert.equal(item.phases.reduce((minutes,[phase])=>minutes+Number(phase.split(" ").at(-2)),0),item.minutes);
    assert.ok(content.children[0].children.some(node=>node.textContent===item.minutes+" min"));
    assert.equal(content.children.length,18);
    assert.ok(content.children[1].children.some(node=>node.textContent===item.standards));
    assert.ok(content.children[2].children.some(node=>node.textContent===item.references));
   }
  }
  assert.equal(lessonNumber,subjectCode==="MATH_DLP"?78:63);
 }
 for(const n of ["1","3","4"]){
  year.value=n;
  await listeners["year.change"]();
  assert.equal(panel.hidden,true);
  assert.deepEqual(subject.options.map(x=>x.label),[
   "Pilih Subjek","Science (DLP) — Dalam Penyediaan","Mathematics (DLP) — Dalam Penyediaan"
  ]);
  for(const option of subject.options.slice(1)){
   subject.value=option.value;
   await listeners["subject.change"]();
   assert.equal(panel.hidden,true);
   assert.match(ctx.help,/Dalam Penyediaan/);
   assert.ok(ctx.catalogStatus.textContent.includes(n==="1"?"Tahun 1 (KP Baharu)":"Tahun "+n));
  }
 }
 assert.deepEqual(catalogueCalls,[]);
 for(const n of ["5","6"]){
  year.value=n;
  await listeners["year.change"]();
  assert.deepEqual(subject.options.map(x=>x.label),[
   "Pilih Subjek","Science (DLP) — RPH 2027","Mathematics (DLP) — RPH 2027"
  ]);
  for(const [code,prefix] of [["SCIENCE_DLP","SCI"],["MATH_DLP","MATH"]]){
   const id=`DLP-${prefix}-Y${n}-L01`;
   subject.value=code;
   await listeners["subject.change"]();
   assert.equal(unit.hidden,false);
   assert.deepEqual(unit.options.map(x=>x.value),["","01"]);
   unit.value="01";
   await listeners["unit.change"]();
   assert.deepEqual(lesson.options.map(x=>x.value),["",id]);
   lesson.value=id;
   listeners["lesson.change"]();
   assert.equal(panel.hidden,true);
   assert.equal(materials.hidden,false);
   assert.deepEqual(catalogueCalls.splice(0),["units",code,"pdp",code,"01"]);
  }
 }
 assert.equal(checkedRph,4);
 curriculum.value="kssr";
 listeners["curriculum.change"]();
 assert.equal(panel.hidden,true);
 assert.equal(subject.hidden,true);
 assert.deepEqual(year.options.map(x=>x.value),["","1","2","3","4","5","6"]);
 year.value="2";
 await listeners["year.change"]();
 assert.deepEqual(subject.options.map(x=>x.value),["","MATH","planned:bahasa_iban",
  "planned:bahasa_kadazandusun","planned:bahasa_semai","planned:bahasa_cina_sk","planned:bahasa_tamil_sk"]);
 for(const option of subject.options.slice(2)){
  subject.value=option.value;
  await listeners["subject.change"]();
  assert.match(ctx.catalogStatus.textContent,/Tahun 2 — Dalam Penyediaan/);
  assert.equal(unit.hidden,true);
  assert.equal(lesson.hidden,true);
 }
 assert.deepEqual(catalogueCalls,["subjects"]);
 subject.value="MATH";
 await listeners["subject.change"]();
 assert.equal(panel.hidden,true);
 assert.deepEqual(catalogueCalls,["subjects","units","MATH"]);
 let resolveOldSubjects;
 ctx.loadOptions=()=>new Promise(resolve=>{resolveOldSubjects=resolve;});
 const pending=listeners["year.change"]();
 curriculum.value="dlp";
 listeners["curriculum.change"]();
 year.value="2";
 await listeners["year.change"]();
 resolveOldSubjects([{value:"MATH",label:"Matematik"}]);
 await pending;
 assert.deepEqual(subject.options.map(x=>x.value),["","SCIENCE_DLP","MATH_DLP"]);
 console.log("WEB_PLANNED_MENUS: PASS (curriculum first, scoped years and subjects, stale request discarded)");
})().catch(error=>{console.error(error);process.exitCode=1;});
