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
assert.match(source,/<select id="curriculum">.*<option value="kssr">KSSR \(SK \/ SJKC \/ SJKT\)<\/option><option value="kp2027">KP2027<\/option><option value="ppki">Pendidikan Khas \(PPKI\)<\/option><\/select>/);
assert.doesNotMatch(source,/<option value="(?:sjkc|sjkt)">KSSR/);
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
const rptRouting=code.slice(code.indexOf("const rptCurricula="),code.indexOf("function rptYearLabel("));
const rptContext=vm.runInNewContext(rptRouting+"\n({rptCurricula,rptCurriculumFor})");
assert.ok(rptContext.rptCurricula.every(([key])=>key!=="dlp"));
assert.equal(rptContext.rptCurriculumFor("matematik_sjkc",2),"kssr");
assert.equal(rptContext.rptCurriculumFor("matematik_sjkt",2),"kssr");
for(const n of [2,3,4,5,6]){
 assert.equal(rptContext.rptCurriculumFor("science_dlp",n),"kssr");
 assert.equal(rptContext.rptCurriculumFor("mathematics_dlp",n),"kssr");
}

const listeners={};
function mockSelect(name){
 return {value:"",options:[],addEventListener(event,fn){listeners[name+"."+event]=fn;}};
}
const curriculum=mockSelect("curriculum"),year=mockSelect("year"),subject=mockSelect("subject"),unit=mockSelect("unit");
const lesson=mockSelect("lesson"),theme=mockSelect("theme"),topic=mockSelect("topic"),component=mockSelect("component");
const catalogueCalls=[];
const catalogStatus={textContent:"",children:[],replaceChildren(...items){this.children=items;this.textContent=items.map(x=>x.textContent||"").join(" ");}};
const makeNode=()=>({textContent:"",children:[],append(...items){this.children.push(...items);},replaceChildren(){this.children=[];}});
assert.doesNotMatch(source,/id="dlp-review-data"|id="dlp-rph-preview"/);
const variantRpt={hidden:true,dataset:{}}, materials={hidden:true,disabled:true};
const materialAccessNotice={hidden:true,textContent:""};
const kpPilotGroup=mockSelect("kp-pilot-group"),kpPilotGroupLabel={hidden:true},kpPilotActions={hidden:true};
const kpPilotStatus={textContent:""};
const kpPilotWord={disabled:true,dataset:{kp2027Format:"word"},addEventListener(event,fn){listeners["kpword."+event]=fn;}};
const kpPilotPdf={disabled:true,dataset:{kp2027Format:"pdf"},addEventListener(event,fn){listeners["kppdf."+event]=fn;}};
const kpPilotRequests=[];
let checkedRph=0;
const variants=[
 {code:"science_dlp",label:"Science (DLP)",rph_code:"SCIENCE_DLP",curriculum:"dlp",rpt_years:[2,3,4,5,6]},
 {code:"mathematics_dlp",label:"Mathematics (DLP)",rph_code:"MATH_DLP",curriculum:"dlp",rpt_years:[2,3,4,5,6]},
 {code:"matematik_sjkc",label:"Matematik (SJKC)",curriculum:"sjkc",rpt_years:[2]},
 {code:"matematik_sjkt",label:"Matematik (SJKT)",curriculum:"sjkt"},
 ...[
  ["bahasa_iban","Bahasa Iban"],["bahasa_kadazandusun","Bahasa Kadazandusun"],
  ["bahasa_semai","Bahasa Semai"],["bahasa_cina_sk","Bahasa Cina (SK)"],["bahasa_tamil_sk","Bahasa Tamil (SK)"]
 ].map(([code,label])=>({code,label,curriculum:"kssr"})),
];
function dlpId(science,n){
 if(n==="2")return science?"DLP-SCI-Y2-U01-01":"DLP-MAT-Y2-U01-01";
 if(n==="3")return science?"DLP-SCI-Y3-01":"DLP-MAT-Y3-U01-01";
 return `DLP-${science?"SCI":n==="4"?"MAT":"MATH"}-Y${n}-L01`;
}
const ctx={
 curriculum,year,subject,unit,lesson,theme,topic,component,catalogStatus,
 window:{cikgulajuSubjectVariants:variants},rphSubjectPicker:{sync(){}},
 document:{createElement:makeNode,createTextNode:text=>({textContent:text}),
  getElementById:id=>({
   "show-materials":materials,"materials-access-status":materialAccessNotice,
   "kp2027-pilot-group":kpPilotGroup,"kp2027-pilot-group-label":kpPilotGroupLabel,
   "kp2027-pilot-downloads":kpPilotActions,"kp2027-pilot-status":kpPilotStatus,
   "kp2027-pilot-word":kpPilotWord,"kp2027-pilot-pdf":kpPilotPdf
  })[id]??variantRpt},
 async fetch(url,options){
  kpPilotRequests.push({url,options});
  if(url.endsWith("/matematik/available"))return {ok:true,json:async()=>({
   groups:{A:[1,2],B:[1]},
   items:{
    A:[{no:1,unit:"Nombor Bulat hingga 100 — Nilai Nombor",tajuk:"Kenal Nombor",sp:"1.1.1"},
       {no:2,unit:"Nombor Bulat hingga 100 — Nilai Nombor",tajuk:"Kenal Nombor",sp:"1.1.1"}],
    B:[{no:1,unit:"Nombor Bulat hingga 100 — Nilai Nombor",tajuk:"Kenal Nombor",sp:"1.1.1"}]
   }
  })};
  if(url.endsWith("/alam-dan-manusia/available"))return {ok:true,json:async()=>({
   lessons:[1,2,38],
   items:[
    {no:1,unit:"Diri Saya dan Keluarga",tajuk:"Anggota Badan Saya",sp:"1.1.1"},
    {no:2,unit:"Diri Saya dan Keluarga",tajuk:"Lagu Anggota Badan",sp:"1.1.2"},
    {no:38,unit:"Inspirasi Alam",tajuk:"Kehendak Berbeza daripada Keperluan",sp:"4.1.7"}
   ]
  })};
  throw Error("Unexpected pilot endpoint: "+url);
 },
 materialPanel:{hidden:true},
 canGenerateRph:()=>true,
 resetSelect(el,label){el.value="";el.options=[{value:"",label}];el.disabled=true;},
 fillSelect(el,items,label){ctx.resetSelect(el,label);el.options.push(...items);el.disabled=!items.length;},
 resetCurriculumChoices(){ctx.resetSelect(unit,"");ctx.resetSelect(lesson,"");unit.hidden=lesson.hidden=variantRpt.hidden=true;delete variantRpt.dataset.subject;},
 setSubjectNavigationLabels(){},
 resetMaterials(){},resetRphPreview(){},showRphAction(){},displayBookReference(){},
 updateSelectionHelp(text){ctx.help=text;},
 async loadOptions(kind,extra={}){
  catalogueCalls.push(kind);
  if(extra.curriculum==="sjkc")return ctx.sjkcReady?[{value:"MATH_SJKC",label:"Matematik SJKC"}]:[];
  if(extra.curriculum==="sjkt")return ctx.sjktReady?[{value:"MATH_SJKT",label:"Matematik SJKT"}]:[];
  return [{value:"MATH",label:"Matematik"}];
 },
 showStep(el,visible){el.hidden=!visible;}, subjectNavLabel(){return "Unit";},
 async fillForSelection(el,kind,extra){
  catalogueCalls.push(kind,extra.subject);
  if(extra.subject==="MATH_DLP")ctx.fillSelect(el,[{value:"01",label:"Unit 1 Whole Numbers and Operations"}],"Pilih Unit");
  if(extra.subject==="SCIENCE_DLP")ctx.fillSelect(el,[{value:"01",label:"Unit 1 Scientific Skills"}],"Pilih Unit");
  if(extra.subject==="MATH_SJKC")ctx.fillSelect(el,[{value:"2",label:"Unit 2 · 基本运算"}],"Pilih Unit");
  if(extra.subject==="MATH_SJKT")ctx.fillSelect(el,[{value:"5",label:"Unit 5 · Masa dan waktu"}],"Pilih Unit");
  return true;
 },
 async loadFinalLesson(kind,extra){
  catalogueCalls.push(kind,extra.subject,extra.unit);
  if(extra.subject==="MATH_SJKC"){
   ctx.fillSelect(lesson,[{value:"17",label:"PdP 017 · 无进退位的加减混合运算"}],"Pilih PdP");
   return;
  }
  if(extra.subject==="MATH_SJKT"){
   ctx.fillSelect(lesson,[{value:"71",label:"PdP 071 · Masa"}],"Pilih PdP");
   return;
  }
  const science=extra.subject==="SCIENCE_DLP";
  ctx.fillSelect(lesson,[{value:dlpId(science,year.value),
    label:science?"Lesson 01 • Observe":"Lesson 01 • Whole Numbers"}],"Pilih Lesson");
 },
 async checkRphAvailability(){checkedRph++;},
};
vm.runInNewContext(code.slice(code.indexOf("const subjectVariants="),code.indexOf("async function loadOptions("))
 +"\n"+code.slice(code.indexOf('curriculum.addEventListener("change"'),code.indexOf('const MATERIAL_CATEGORIES'))
 +"\n"+code.slice(code.indexOf("function syncRphMaterialsAccess("),code.indexOf("function materialRow("))
,ctx);
(async()=>{
 listeners["curriculum.change"]();
 assert.equal(year.hidden,true);
 assert.equal(subject.hidden,true);
 curriculum.value="kp2027";
 listeners["curriculum.change"]();
 assert.deepEqual(year.options.map(x=>x.label),["Pilih Tahun","Tahun 1 (KP Baharu)"]);
 year.value="1";
 await listeners["year.change"]();
 assert.equal(subject.disabled,false);
 assert.equal(subject.hidden,false);
 assert.deepEqual(subject.options.map(x=>x.value),["","MATH_KP2027","ALAM_KP2027","BM_SK_KP2027","PJ_KP2027"]);
 assert.match(ctx.help,/Download Word\/PDF/i);
 assert.match(ctx.catalogStatus.textContent,/Alam dan Manusia/);
 assert.deepEqual(catalogueCalls,[]);
 subject.value="MATH_KP2027";
 await listeners["subject.change"]();
 assert.equal(kpPilotRequests.at(-1).url,"/api/kp2027/sk/tahun-1/matematik/available");
 assert.equal(unit.hidden,false);
 assert.equal(lesson.hidden,true);
 assert.deepEqual(unit.options.map(x=>x.value),["","Nombor Bulat hingga 100 — Nilai Nombor"]);
 assert.equal(kpPilotGroup.hidden,false);
 assert.equal(kpPilotActions.hidden,true);
 assert.equal(kpPilotWord.disabled,true);
 unit.value="Nombor Bulat hingga 100 — Nilai Nombor";
 await listeners["unit.change"]();
 assert.equal(lesson.hidden,false);
 assert.deepEqual(lesson.options.map(x=>x.value),["","1","2"]);
 assert.match(lesson.options[1].label,/^PdP 001 — Kenal Nombor • SP 1[.]1[.]1$/);
 lesson.value="1";
 listeners["lesson.change"]();
 assert.equal(materials.hidden,false);
 assert.equal(kpPilotActions.hidden,true);
 kpPilotGroup.value="B";
 listeners["kp-pilot-group.change"]();
 assert.equal(lesson.hidden,true);
 assert.equal(unit.value,"");
 unit.value="Nombor Bulat hingga 100 — Nilai Nombor";
 await listeners["unit.change"]();
 assert.deepEqual(lesson.options.map(x=>x.value),["","1"]);
 assert.equal(kpPilotWord.disabled,true);
 subject.value="ALAM_KP2027";
 await listeners["subject.change"]();
 assert.equal(kpPilotRequests.at(-1).url,"/api/kp2027/sk/tahun-1/alam-dan-manusia/available");
 assert.deepEqual(unit.options.map(x=>x.value),["","Diri Saya dan Keluarga","Inspirasi Alam"]);
 assert.equal(lesson.hidden,true);
 assert.equal(kpPilotGroup.hidden,true);
 assert.equal(kpPilotActions.hidden,true);
 unit.value="Inspirasi Alam";
 await listeners["unit.change"]();
 assert.deepEqual(lesson.options.map(x=>x.value),["","38"]);
 assert.match(lesson.options[1].label,/RPH sumber 038 — Kehendak Berbeza daripada Keperluan/);
 lesson.value="38";
 listeners["lesson.change"]();
 assert.equal(materials.hidden,false);
 assert.equal(catalogueCalls.length,0);
 assert.match(ctx.catalogStatus.textContent,/RPH sumber 038/);
 curriculum.value="kssr";
 listeners["curriculum.change"]();
 assert.deepEqual(year.options.map(x=>x.value),["","1","2","3","4","5","6"]);
 for(const y of ["2","3"]){
  year.value=y;await listeners["year.change"]();
  assert.ok(subject.options.some(o=>o.value==="MATH"&&o.label==="Matematik (SK)"));
  const pending=subject.options.find(o=>o.value==="matematik_sjkc");
  assert.ok(pending,"Year "+y+" SJKC planned subject");
  assert.match(pending.label,/Matematik \(SJKC\).*Dalam Penyediaan/);
  subject.value=pending.value;await listeners["subject.change"]();
  assert.equal(unit.hidden,true);assert.equal(lesson.hidden,true);
  assert.match(ctx.help,/dalam penyediaan/i);
 }
 assert.deepEqual(catalogueCalls.splice(0),["subjects","subjects","subjects","subjects","subjects"]);
 ctx.sjkcReady=true;
 for(const y of ["2","3"]){
  year.value=y;await listeners["year.change"]();
  const option=subject.options.find(o=>o.value==="MATH_SJKC");
  assert.ok(option);assert.equal(option.label,"Matematik (SJKC)");
  subject.value="MATH_SJKC";await listeners["subject.change"]();
  assert.deepEqual(unit.options.map(o=>o.value),["","2"]);
  unit.value="2";await listeners["unit.change"]();
  assert.deepEqual(lesson.options.map(o=>o.value),["","17"]);
 }
 assert.deepEqual(catalogueCalls.splice(0),[
  "subjects","subjects","subjects","units","MATH_SJKC","pdp","MATH_SJKC","2",
  "subjects","subjects","units","MATH_SJKC","pdp","MATH_SJKC","2"]);
 year.value="2";await listeners["year.change"]();
 const draftSjkt=subject.options.find(o=>o.value==="matematik_sjkt");
 assert.ok(draftSjkt);assert.match(draftSjkt.label,/Matematik \(SJKT\).*Dalam Penyediaan/);
 subject.value=draftSjkt.value;await listeners["subject.change"]();
 assert.equal(unit.hidden,true);
 ctx.sjktReady=true;await listeners["year.change"]();
 const sjktOption=subject.options.find(o=>o.value==="MATH_SJKT");
 assert.ok(sjktOption);assert.equal(sjktOption.label,"Matematik (SJKT)");
 subject.value=sjktOption.value;await listeners["subject.change"]();
 assert.deepEqual(unit.options.map(o=>o.value),["","5"]);
 unit.value="5";await listeners["unit.change"]();
 assert.deepEqual(lesson.options.map(o=>o.value),["","71"]);
 assert.deepEqual(catalogueCalls.splice(0),[
  "subjects","subjects","subjects","subjects","subjects","subjects",
  "units","MATH_SJKT","pdp","MATH_SJKT","5"]);
 curriculum.value="kssr";
 listeners["curriculum.change"]();
 assert.deepEqual(year.options.map(x=>x.value),["","1","2","3","4","5","6"]);
 year.value="1";
 await listeners["year.change"]();
 assert.ok(subject.options.every(item=>!item.value.endsWith("_DLP")));
 subject.value="MATH_DLP";
 await listeners["subject.change"]();
 assert.equal(variantRpt.hidden,true);
 assert.equal(unit.hidden,true);
 assert.deepEqual(catalogueCalls.splice(0),["subjects"]);
 for(const n of ["2","3","4","5","6"]){
  year.value=n;
  await listeners["year.change"]();
  assert.deepEqual(subject.options.filter(x=>x.value.endsWith("_DLP")).map(x=>x.label),
   ["Science (DLP)","Mathematics (DLP)"]);
  assert.ok(subject.options.some(item=>item.value==="MATH"));
  assert.deepEqual(catalogueCalls.splice(0),n==="2"?["subjects","subjects","subjects"]:n==="3"?["subjects","subjects"]:["subjects"]);
  for(const code of ["SCIENCE_DLP","MATH_DLP"]){
   const id=dlpId(code==="SCIENCE_DLP",n);
   subject.value=code;
   await listeners["subject.change"]();
   assert.equal(unit.hidden,false);
   assert.equal(variantRpt.hidden,false);
   assert.equal(variantRpt.dataset.subject,code==="SCIENCE_DLP"?"science_dlp":"mathematics_dlp");
   assert.doesNotMatch(ctx.catalogStatus.textContent,/Alam dan Manusia/);
   assert.deepEqual(unit.options.map(x=>x.value),["","01"]);
   unit.value="01";
   await listeners["unit.change"]();
   assert.deepEqual(lesson.options.map(x=>x.value),["",id]);
   lesson.value=id;
   listeners["lesson.change"]();
   assert.equal(materials.hidden,false);
   assert.deepEqual(catalogueCalls.splice(0),["units",code,"pdp",code,"01"]);
  }
 }
 assert.equal(checkedRph,10);
 curriculum.value="kssr";
 listeners["curriculum.change"]();
 assert.equal(subject.hidden,true);
 assert.deepEqual(year.options.map(x=>x.value),["","1","2","3","4","5","6"]);
 year.value="2";
 await listeners["year.change"]();
 assert.ok(subject.options.some(o=>o.value==="MATH"&&o.label==="Matematik (SK)"));
 assert.ok(subject.options.some(o=>o.value==="MATH_SJKC"));
 assert.ok(subject.options.some(o=>o.value==="MATH_SJKT"));
 for(const option of subject.options.filter(item=>item.value.startsWith("planned:"))){
  subject.value=option.value;
  await listeners["subject.change"]();
  assert.match(ctx.catalogStatus.textContent,/Tahun 2 — Dalam Penyediaan/);
  assert.equal(unit.hidden,true);
  assert.equal(lesson.hidden,true);
 }
 assert.deepEqual(catalogueCalls,["subjects","subjects","subjects"]);
 subject.value="MATH";
 await listeners["subject.change"]();
 assert.deepEqual(catalogueCalls,["subjects","subjects","subjects","units","MATH"]);
 const resolveOldSubjects=[];
 ctx.loadOptions=()=>new Promise(resolve=>{resolveOldSubjects.push(resolve);});
 const pending=listeners["year.change"]();
 curriculum.value="kp2027";
 listeners["curriculum.change"]();
 year.value="1";
 await listeners["year.change"]();
 for(const resolve of resolveOldSubjects)resolve([{value:"MATH",label:"Matematik"}]);
 await pending;
 assert.deepEqual(subject.options.map(x=>x.value),["","MATH_KP2027","ALAM_KP2027","BM_SK_KP2027","PJ_KP2027"]);
 assert.match(ctx.catalogStatus.textContent,/Alam dan Manusia/);
 console.log("WEB_PLANNED_MENUS: PASS (curriculum first, scoped years and subjects, stale request discarded)");
})().catch(error=>{console.error(error);process.exitCode=1;});
