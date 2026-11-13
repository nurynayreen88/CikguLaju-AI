/* RPH Hari Ini: independent source-backed cascading dropdowns for every
 * teachable timetable slot. One Jana Bahan discovers resources for all
 * selections; a download remains per Lesson and uses the native Telegram
 * endpoint/quota. No guessed lesson, duplicate catalog or batch trial debit.
 */
(()=>{
 "use strict";
 const dateInput=document.getElementById("today-date");
 const refresh=document.getElementById("today-refresh");
 const state=document.getElementById("today-status");
 const list=document.getElementById("today-list");
 const confirm=document.getElementById("today-confirm-school-day");
 const confirmWrap=document.getElementById("today-confirm-wrap");
 const manual=document.getElementById("today-manual");
 const generateAll=document.getElementById("today-generate-all");
 const allStatus=document.getElementById("today-generate-status");
 const resultsHost=document.getElementById("today-results");
 const resultsList=document.getElementById("today-results-list");
 if(!dateInput||!refresh||!state||!list||!confirm||!generateAll||
    !allStatus||!resultsHost||!resultsList)return;
 let requestId=0,loadedDate="",loading=false,reviewing=false,choices=[],batchEpoch=0;
 const cache=new Map(),rosterCounts=new Map();
 const TAGS=["component","theme","unit","topic","lesson"];
 const SOURCE_NAMES={
  BM:"Unit",ENGLISH:"Unit / Topic",PI:"Bidang / Tajuk",
  MATH:"Bidang / Unit",SCIENCE:"Tema / Unit",MORAL:"Unit / Nilai",
  PSV:"Bidang / Unit",PJPK:"Unit / Tajuk",ARAB:"Unit",
  MUZIK:"Unit / Tajuk",SEJARAH:"Unit",RBT:"Unit"
 };
 const TYPES=new Set(["textbook","workbook","audio"]);
 const musicLink=/^https:\/\/drive\.google\.com\/file\/d\/[A-Za-z0-9_-]{10,100}\/view\?usp=drivesdk$/;

 function create(tag,cls,value){
  const el=document.createElement(tag);
  if(cls)el.className=cls;
  if(value!==undefined)el.textContent=String(value);
  return el;
 }
 function nativeUnitLabel(raw,code){
  const value=String(raw||"").trim();
  const numbered=/^(?:Unit|U)\s*0*([1-9][0-9]{0,2})\s*(?:[:：.\-–—•]\s*)?(.+)$/i.exec(value);
  if(numbered)return "Unit "+Number(numbered[1])+": "+numbered[2].trim();
  const dot=/^([1-9][0-9]{0,2})\s*[•·]\s*(.+)$/.exec(value);
  if(dot&&["MATH","SCIENCE"].includes(code))return "Unit "+Number(dot[1])+": "+dot[2].trim();
  return value;
 }
 function nativeLessonLabel(item,code){
  let text=String(item.label||"").trim();
  if(!/^(?:PdP|Lesson)\s*0*[1-9][0-9]*/i.test(text)){
   const n=item.pdp_no??item.lesson_no??item.sequence_no;
   if(Number.isInteger(n)&&n>0&&n<10000)
    text=(code==="ENGLISH"?"Lesson ":"PdP ")+String(n).padStart(3,"0")+" — "+text;
  }
  if(!/^(?:Lesson|PdP)\s*0*[1-9][0-9]*(?:\b|\s|[•—–:-])/i.test(text))return "";
  const book=String(item.textbook_ref||item.student_book_ref||"").trim();
  if(book&&!text.includes(book))text+=" • "+book;
  return text;
 }
 function updateAll(){
  const selectable=choices.filter(c=>c.slot.can_prepare);
  const incomplete=selectable.filter(c=>!c.controls.lesson.value);
  const busy=selectable.some(c=>c.busy);
  // Keep the original all-slots guard, covered by existing RPH Hari Ini QA.
  generateAll.disabled=loading||reviewing||!confirm.checked||!selectable.length||
   selectable.some(c=>c.busy||!c.controls.lesson.value);
  for(const c of choices){
   for(const name of TAGS){
    const select=c.controls[name];
    if(select&&!select.hidden&&select.dataset.ready==="1")
     select.disabled=reviewing||!select.dataset.hasOptions;
   }
  }
  // Inform teachers why batch generation is disabled without changing the
  // existing button, selection flow, or any generation/credit endpoints.
  // Only saved timetable slot labels and source-backed selection states appear.
  if(!loading&&!reviewing&&resultsHost.hidden){
   const done=selectable.length-incomplete.length;
   if(!selectable.length){
    allStatus.textContent=choices.length
     ?"Tiada slot dengan bahan disahkan untuk disediakan pada tarikh ini.":"";
   }else if(busy){
    allStatus.textContent=done+" daripada "+selectable.length+
     " slot lengkap. Sedang menyemak pilihan kurikulum…";
   }else if(incomplete.length){
    const first=incomplete[0];
    const noSource=Boolean(first.message.textContent)&&
     first.controls.lesson.dataset.hasOptions!=="1";
    allStatus.textContent=done+" daripada "+selectable.length+
     " slot lengkap. "+(noSource
      ?"Semak pilihan sumber untuk "+first.slot.class_name+" ("+first.slot.subject+")."
      :"Pilih Lesson/PdP untuk "+first.slot.class_name+" ("+first.slot.subject+").")+
     (incomplete.length>1?" Baki "+incomplete.length+" slot belum lengkap.":"");
   }else if(!confirm.checked){
    allStatus.textContent=done+" daripada "+selectable.length+
     " slot lengkap. Sahkan hari PdP sebenar untuk meneruskan.";
   }else{
    allStatus.textContent=done+" daripada "+selectable.length+
     " slot lengkap. Tekan Jana Bahan Semua Lesson untuk menyemak bahan.";
   }
  }
 }
 function clearResults(){
  batchEpoch++;
  resultsHost.hidden=true;
  resultsList.replaceChildren();
  for(const c of choices){
   if(!c.result)continue;
   c.result.hidden=true;
   c.downloadStatus.textContent="";
   c.resultList.replaceChildren();
  }
  allStatus.textContent="";
  updateAll();
 }
 function resetFrom(c,field){
  const start=TAGS.indexOf(field);
  for(let i=start;i<TAGS.length;i++){
   const name=TAGS[i],select=c.controls[name];
   select.replaceChildren(new Option("Pilih "+(name==="lesson"?"Lesson/PdP":name),""));
   select.value="";
   select.dataset.ready="0";
   select.dataset.hasOptions="";
   select.disabled=true;
   select.parentNode.hidden=true;
  }
  clearResults();
 }
 function stage(c,name,label){
  const wrap=create("div","daily-rph-field");
  const caption=create("label","",label);
  const id="today-"+c.index+"-"+name;
  caption.htmlFor=id;
  const select=create("select","daily-rph-select");
  select.id=id;
  select.dataset.ready="0";
  select.append(new Option("Pilih "+label,""));
  select.disabled=true;
  wrap.hidden=true;
  wrap.append(caption,select);
  c.editor.append(wrap);
  c.controls[name]=select;
  select.addEventListener("change",()=>{void advance(c,name);});
  return select;
 }
 function fill(c,name,items,label){
  const select=c.controls[name];
  select.replaceChildren(new Option("Pilih "+label,""));
  for(const item of items){
   if(item.value==null||!item.label)continue;
   let title=String(item.label);
   if(name==="unit")title=nativeUnitLabel(title,c.slot.subject_code);
   if(name==="lesson"){
    title=nativeLessonLabel(item,c.slot.subject_code);
    if(!title)continue;
   }
   const option=new Option(title,String(item.value));
   if(name==="lesson"){
     option.dataset.bookRef=String(item.textbook_ref||item.student_book_ref||"").trim();
     option.dataset.originUnit=String(item.origin_unit||"");
    }
   select.add(option);
  }
  select.parentNode.hidden=false;
  select.dataset.ready="1";
  select.dataset.hasOptions=select.options.length>1?"1":"";
  select.disabled=select.options.length<=1||reviewing;
  if(select.options.length<=1)c.message.textContent="Tiada pilihan yang disahkan untuk "+label+".";
  updateAll();
 }
 async function sourceOptions(year,kind,extra={}){
  const params=new URLSearchParams({kind,year:String(year),...extra});
  const key=params.toString();
  if(!cache.has(key)){
   const task=fetch("/api/options?"+key,{
    credentials:"same-origin",cache:"no-store",redirect:"error"
   }).then(async response=>{
    if(!response.ok)throw Error("Katalog utama belum tersedia (HTTP "+response.status+").");
    const items=await response.json();
    if(!Array.isArray(items)||items.length>250)throw Error("Senarai sumber tidak sah.");
    return items;
   });
   cache.set(key,task);
   task.catch(()=>cache.delete(key));
  }
  return cache.get(key);
 }
 function clearAfter(c,name){
  const idx=TAGS.indexOf(name);
  if(idx<0)resetFrom(c,"component");
  else if(idx+1<TAGS.length)resetFrom(c,TAGS[idx+1]);
  else clearResults();
 }
 async function loadStage(c,name,kind,extra={},label){
  const rev=++c.rev;
  c.busy=true;c.message.textContent="Memuatkan "+label+"…";updateAll();
  try{
   const items=await sourceOptions(c.slot.year,kind,extra);
   if(rev!==c.rev||c.ticket!==requestId)return false;
   fill(c,name,items,label);
   if(items.length)c.message.textContent="";
   return true;
  }catch(error){
   if(rev===c.rev&&c.ticket===requestId)c.message.textContent=error.message;
   return false;
  }finally{
   if(rev===c.rev){c.busy=false;updateAll();}
  }
 }
 async function advance(c,from){
  c.rev++;
  clearAfter(c,from);
  c.reflection.value="";
  c.reflectionPanel.open=false;
  const code=c.slot.subject_code,control=c.controls;
  if(from==="lesson"){
   const chosen=control.lesson.selectedOptions[0];
   c.bookRef.textContent=chosen?.dataset.bookRef?"Rujukan buku: "+chosen.dataset.bookRef:"";
   c.message.textContent=control.lesson.value?"Lesson/PdP telah dipilih.":"";
   updateAll();return;
  }
  c.bookRef.textContent="";
  c.message.textContent="";
  if(from==="subject"){
   if(code==="PJPK"){
    if(await loadStage(c,"component","components",{subject:code},"PJ atau PK")
       &&c.slot.component&&["PJ","PK"].includes(c.slot.component)
       &&[...control.component.options].some(o=>o.value===c.slot.component)){
      control.component.value=c.slot.component;
      await advance(c,"component");
     }
   }else if(code==="BM"){
    await loadStage(c,"theme","bm-themes",{subject:"BM"},"Tema");
   }else{
    await loadStage(c,"unit","units",{subject:code},SOURCE_NAMES[code]||"Unit / Tajuk");
   }
  }else if(from==="component"&&control.component.value){
   await loadStage(c,"unit","units",{subject:code,component:control.component.value},"Unit");
  }else if(from==="theme"&&control.theme.value){
   await loadStage(c,"unit","bm-units",{subject:"BM",theme:control.theme.value},"Unit");
  }else if(from==="unit"&&control.unit.value){
   if(code==="BM"){
    await loadStage(c,"topic","bm-topics",{subject:"BM",theme:control.theme.value,unit:control.unit.value},"Tajuk");
   }else{
    const extra={subject:code,unit:control.unit.value};
    if(code==="PJPK")extra.component=control.component.value;
    await loadStage(c,"lesson","pdp",extra,code==="ENGLISH"?"Lesson":"PdP");
   }
  }else if(from==="topic"&&control.topic.value){
   await loadStage(c,"lesson","bm-pdp",{
    subject:"BM",theme:control.theme.value,unit:control.unit.value,topic:control.topic.value
   },"PdP");
  }
 }
 async function initialize(c){
  c.busy=true;updateAll();
  try{
   const items=await sourceOptions(c.slot.year,"subjects");
   if(c.ticket!==requestId)return;
   if(!items.some(x=>x.value===c.slot.subject_code)){
    c.message.textContent="Subjek jadual belum tersedia dalam katalog sumber untuk Tahun "+c.slot.year+".";
    return;
   }
   await advance(c,"subject");
  }catch(error){if(c.ticket===requestId)c.message.textContent=error.message;}
  finally{c.busy=false;updateAll();}
 }
 function makeChoice(slot,index,ticket){
  const card=create("article","daily-rph-card");
  const heading=create("div","daily-rph-card-top");
  heading.append(create("strong","",slot.class_name+" · "+slot.subject),
                 create("span","daily-rph-time",slot.start+" – "+slot.end));
  card.append(heading);
  const subjectLabel=slot.subject_code==="ENGLISH"?"Bahasa Inggeris (SK)":slot.subject;
  const info=create("p","daily-rph-note","Tahun "+slot.year+" · "+subjectLabel);
  card.append(info);
  const c={slot,index,ticket,card,rev:0,busy:false,controls:{}};
  if(!slot.can_prepare){
   card.append(create("p","notice",slot.reason||"Waktu ini tidak mempunyai padanan sumber yang disahkan."));
   list.append(card);
   return c;
  }
  c.editor=create("div","daily-rph-editor");
  c.editor.append(create("h3","","Pilih Tajuk / Topik / Lesson"));
  c.message=create("p","notice");
  c.bookRef=create("p","notice");
  for(const [name,label] of [
   ["component","Komponen PJ atau PK"],["theme","Tema"],["unit",SOURCE_NAMES[slot.subject_code]||"Unit / Tajuk"],
   ["topic","Tajuk"],["lesson",slot.subject_code==="ENGLISH"?"Lesson":"PdP"]
  ])stage(c,name,label);
  c.students=create("input");
  c.students.type="number";
  c.students.min="1";
  c.students.max="200";
  c.students.step="1";
  c.students.inputMode="numeric";
  c.students.id="daily-rph-students-"+index;
  const countLabel=create("label","","Bilangan Murid");
  countLabel.htmlFor=c.students.id;
  const countHint=create("p","notice","Guru boleh ubah jumlah untuk RPH ini.");
  countHint.id=c.students.id+"-hint";
  c.students.setAttribute("aria-describedby",countHint.id);
  c.students.placeholder="Ikut Rekod PBD";
  const schoolYear=loadedDate.slice(0,4);
  if(!rosterCounts.has(slot.class_name)){
   rosterCounts.set(slot.class_name,readPbdRosterCount(slot.class_name,schoolYear).catch(()=>null));
  }
  void rosterCounts.get(slot.class_name).then(count=>{
   if(ticket!==requestId)return;
   if(count)c.students.placeholder=String(count)+" daripada Rekod PBD";
   else countHint.textContent=count===0?"Senarai murid sesi "+schoolYear+" masih kosong. Guru boleh isi jumlah di sini.":
    "Rekod PBD belum dapat disemak. Guru boleh isi jumlah di sini.";
  });
  c.reflectionPanel=create("details","rph-reflection");
  c.reflection=create("textarea");
  c.reflection.rows=3;
  c.reflection.maxLength=500;
  c.reflection.id="daily-rph-reflection-"+index;
  const reflectionLabel=create("label","","Refleksi guru");
  reflectionLabel.htmlFor=c.reflection.id;
  const reflectionHint=create("p","notice","Maksimum 500 aksara dan 6 baris. Biarkan kosong untuk menggunakan ruangan refleksi sedia ada.");
  reflectionHint.id=c.reflection.id+"-hint";
  c.reflection.setAttribute("aria-describedby",reflectionHint.id);
  c.reflectionPanel.append(create("summary","","Tulis refleksi sendiri (pilihan)"),reflectionLabel,c.reflection,reflectionHint);
  c.editor.append(c.bookRef,c.message,countLabel,c.students,countHint,c.reflectionPanel);
  card.append(c.editor);
  // Result cards are deliberately NOT appended inside the selection cards.
  // They are rendered in a single output area after the *entire* timetable.
  c.result=create("article","daily-rph-result-card");
  c.result.hidden=true;
  const resultHeading=create("div","daily-rph-card-top");
  resultHeading.append(
   create("strong","",slot.class_name+" · "+slot.subject),
   create("span","daily-rph-time",slot.start+" – "+slot.end)
  );
  c.resultSelection=create("p","daily-rph-selection");
  c.result.append(resultHeading,c.resultSelection,
                  create("h4","","Bahan tersedia"));
  c.resultList=create("ul","daily-rph-materials");
  c.downloadStatus=create("p","notice");
  c.result.append(c.resultList,c.downloadStatus);
  list.append(card);
  void initialize(c);
  return c;
 }
 function render(data,ticket){
  loadedDate=data.date;
  dateInput.value=data.date;
  confirm.checked=false;
  confirmWrap.hidden=!data.count;
  resultsHost.hidden=true;
  resultsList.replaceChildren();
  list.replaceChildren();
  choices=[];
  if(!data.count)list.append(create("p","notice",
   "Tiada waktu mengajar pada "+data.day+". Pilih tarikh lain atau kemas kini Jadual Waktu di Profil Guru."));
  for(const [i,slot] of data.entries.entries())choices.push(makeChoice(slot,i,ticket));
  state.textContent=data.day+", "+new Intl.DateTimeFormat("ms-MY",{
   timeZone:"Asia/Kuala_Lumpur",day:"numeric",month:"long",year:"numeric"
  }).format(new Date(data.date+"T12:00:00+08:00"))+
   " · "+data.count+" waktu dalam jadual. "+data.holiday_notice;
  updateAll();
 }
 async function load(date=""){
  const ticket=++requestId;
  cache.clear();
  rosterCounts.clear();
  batchEpoch++;
  loading=true;reviewing=false;choices=[];
  resultsHost.hidden=true;
  resultsList.replaceChildren();
  list.replaceChildren();
  confirm.checked=false;confirmWrap.hidden=true;
  refresh.disabled=true;
  generateAll.disabled=true;
  allStatus.textContent="";
  state.textContent="Membaca jadual waktu daripada Profil Guru…";
  try{
   const qs=date?"?"+new URLSearchParams({date}):"";
   const response=await fetch("/api/web/rph/hari-ini"+qs,{
    credentials:"same-origin",cache:"no-store",redirect:"error"
   });
   const data=await response.json().catch(()=>({}));
   if(ticket!==requestId)return;
   if(!response.ok)throw Error(data.error||"Jadual belum tersedia (HTTP "+response.status+").");
   if(!Array.isArray(data.entries)||typeof data.date!=="string")throw Error("Format jadual tidak sah.");
   render(data,ticket);
  }catch(error){
   if(ticket!==requestId)return;
   choices=[];state.textContent=error.message;
  }finally{
   if(ticket===requestId){loading=false;refresh.disabled=false;updateAll();}
  }
 }
 function selection(c){
  const v=c.controls;
  const params={year:String(c.slot.year),subject:c.slot.subject_code,
                unit:v.lesson.selectedOptions[0]?.dataset.originUnit||v.unit.value,
                lesson:v.lesson.value};
  if(c.slot.subject_code==="PJPK")params.component=v.component.value;
  return params;
 }
 function selectedKey(c){return JSON.stringify({date:loadedDate,...selection(c)});}
 function actionRow(name,action,url=null){
  const li=create("li","material-download-row");
  li.append(create("span","material-download-name",name));
  const button=create(url?"a":"button","material-download-action",action);
  if(url){button.href=url;button.target="_blank";button.rel="noopener";}
  li.append(button);
  return {li,button};
 }
 function readyMaterialLink(item,subject){
  if(!item||!TYPES.has(item.type)||typeof item.title!=="string"||
     typeof item.url!=="string"||!item.title.trim())return false;
  if(item.type==="workbook")return item.url.startsWith("/api/web/rph/english-workbook?");
  if(item.type==="textbook")return item.url.startsWith("/api/web/rph/english-student-book?")||
    (subject==="SCIENCE"&&item.url.startsWith("/api/web/rph/science-textbook?"));
  if(item.type==="audio")return /^\/api\/web\/rph\/english-audio\/[1-4]\?/.test(item.url)||musicLink.test(item.url);
  return false;
 }
 async function inspectOne(c,epoch){
  const key=selectedKey(c),args=selection(c),qs=new URLSearchParams(args);
  c.result.hidden=false;c.resultList.replaceChildren();
  c.downloadStatus.textContent="Menyemak bahan yang tersedia…";
  let found=0, errors=[];
  try{
   const availability=await fetch("/api/web/rph/availability?"+qs,{
    credentials:"same-origin",cache:"no-store",redirect:"error"
   });
   const data=await availability.json().catch(()=>({}));
   if(epoch!==batchEpoch||key!==selectedKey(c))return;
   if(availability.ok&&data.available===true&&data.generator==="telegram-native"){
    const pbd=actionRow("Pentaksiran Bilik Darjah","Rekod PBD");
    pbd.button.addEventListener("click",()=>window.cikgulajuPbdFromRph?.({
      className:c.slot.class_name,date:loadedDate,subject:c.slot.subject,
      lesson:c.controls.lesson.selectedOptions[0]?.textContent||""
    },args));
    c.resultList.append(pbd.li);found++;
    const formats=Array.isArray(data.formats)?data.formats.filter(f=>["pdf","word"].includes(f)):["pdf","word"];
    for(const format of ["pdf","word"]){
     if(!formats.includes(format))continue;
     const label=format==="pdf"?"RPH PDF":"RPH Word";
     const row=actionRow(label,data.download_allowed===false?"Akses diperlukan":"Download");
     if(data.download_allowed===false){row.button.disabled=true;}
     else row.button.addEventListener("click",()=>{void downloadRph(c,format,key,row.button);});
     c.resultList.append(row.li);found++;
    }
   }else if(!availability.ok&&availability.status!==404)
    errors.push(data.error||"Semakan RPH tidak berjaya.");
  }catch(_error){errors.push("Semakan RPH tidak dapat dihubungi.");}
  if(epoch!==batchEpoch||key!==selectedKey(c))return;
  if((c.slot.subject_code==="ENGLISH"&&[2,3,4,5,6].includes(c.slot.year))||
      c.slot.subject_code==="MUZIK"||(c.slot.subject_code==="SCIENCE"&&[2,3].includes(c.slot.year))){
   try{
    const params=new URLSearchParams({year:args.year,subject:args.subject,unit:args.unit,lesson:args.lesson});
    const response=await fetch("/api/web/rph/extra-materials?"+params,{
      credentials:"same-origin",cache:"no-store",redirect:"error"
    });
    const data=await response.json().catch(()=>({}));
    if(epoch!==batchEpoch||key!==selectedKey(c))return;
    if(response.ok&&Array.isArray(data.items)&&data.items.length<=30){
     for(const item of data.items){
      if(!readyMaterialLink(item,c.slot.subject_code))continue;
      const label=item.title;
      const action=item.type==="audio"&&musicLink.test(item.url)?"Buka Audio Sumber":"Download";
      const row=actionRow(label,action,item.url);
      c.resultList.append(row.li);found++;
     }
    }else if(!response.ok)errors.push("Bahan tambahan tidak dapat disahkan.");
   }catch(_error){errors.push("Bahan tambahan tidak dapat disemak.");}
  }
  if(epoch!==batchEpoch||key!==selectedKey(c))return;
  c.downloadStatus.textContent=errors.join(" ")||
   (found?"Hanya bahan yang telah disahkan tersedia dipaparkan.":"Tiada bahan yang disahkan tersedia untuk Lesson/PdP ini.");
 }
 async function downloadRph(c,format,key,button){
  if(reviewing||key!==selectedKey(c)||!confirm.checked)return;
  const students=c.students.value.trim();
  if(!c.students.checkValidity()||(students&&!/^[1-9][0-9]{0,2}$/.test(students))){
   c.downloadStatus.textContent="Masukkan bilangan murid antara 1 hingga 200.";
   c.students.reportValidity();
   return;
  }
  const args=selection(c);
  const params=new URLSearchParams({
   year:args.year,subject:args.subject,unit:args.unit,lesson:args.lesson,
   teacher_class:c.slot.class_name,teacher_date:loadedDate,
   teacher_start:c.slot.start,teacher_end:c.slot.end,teacher_students:students
  });
  if(args.component)params.set("component",args.component);
  const expected=params.toString();
  button.disabled=true;
  c.downloadStatus.textContent="Menjana RPH "+format.toUpperCase()+" menggunakan penjana Telegram…";
  try{
   const response=await fetch("/api/web/rph/"+format+"?"+expected,rphDownloadOptions(c.reflection.value));
   if(!response.ok){
    const body=await response.json().catch(()=>({}));
    throw Error(body.error||"Muat turun RPH gagal (HTTP "+response.status+").");
   }
   const mime=(response.headers.get("content-type")||"").toLowerCase();
   const okMime=format==="pdf"?mime.includes("application/pdf"):
    mime.includes("application/vnd.openxmlformats-officedocument.wordprocessingml.document");
   const blob=await response.blob();
   if(!okMime||blob.size<1000)throw Error("Fail RPH yang diterima tidak sah.");
   if(key!==selectedKey(c))throw Error("Pilihan Lesson telah berubah. Semak semula sebelum muat turun.");
   const url=URL.createObjectURL(blob),anchor=document.createElement("a");
   const safeClass=c.slot.class_name.replace(/[^a-z0-9_-]+/gi,"_").slice(0,45);
   anchor.href=url;anchor.download="CIKGULAJU_RPH_"+safeClass+"_"+args.subject+"_"+format+"."+(format==="pdf"?"pdf":"docx");
   document.body.append(anchor);anchor.click();anchor.remove();
   setTimeout(()=>URL.revokeObjectURL(url),30000);
   c.downloadStatus.textContent="RPH "+format.toUpperCase()+" disediakan untuk "+c.slot.class_name+".";
   window.refreshSharedRphBalance?.();
  }catch(error){c.downloadStatus.textContent=error.message;}
  finally{button.disabled=false;}
 }
 async function generate(){
  if(generateAll.disabled)return;
  const selected=choices.filter(c=>c.slot.can_prepare);
  if(!selected.length||selected.some(c=>!c.controls.lesson.value))return;
  reviewing=true;generateAll.disabled=true;updateAll();
  const epoch=++batchEpoch;
  // Keep the same chronological subject/class ordering as the upper cards.
  // Output is one grouped section beneath all subject selectors, not inline.
  resultsList.replaceChildren();
  for(const c of selected){
   const chosen=c.controls.lesson.selectedOptions[0];
   c.resultSelection.textContent="Tahun "+c.slot.year+
     " · "+(chosen?.textContent||"Lesson/PdP dipilih");
   c.result.hidden=false;
   resultsList.append(c.result);
  }
  resultsHost.hidden=false;
  allStatus.textContent="Menyemak bahan bagi "+selected.length+" Lesson/PdP yang dipilih…";
  const queue=selected.slice();
  const workers=Array.from({length:Math.min(3,queue.length)},async()=>{
   while(queue.length&&epoch===batchEpoch){
    const c=queue.shift();
    await inspectOne(c,epoch);
   }
  });
  try{await Promise.all(workers);}
  finally{
   if(epoch===batchEpoch){
    reviewing=false;
    allStatus.textContent="Semakan bahan selesai. Semua bahan dipaparkan di bawah mengikut kelas dan subjek.";
    updateAll();
    resultsHost.scrollIntoView({behavior:"smooth",block:"start"});
   }
  }
 }
 confirm.addEventListener("change",()=>{
  if(!confirm.checked){reviewing=false;clearResults();}
  updateAll();
 });
 refresh.addEventListener("click",()=>{void load(dateInput.value);});
 dateInput.addEventListener("change",()=>{void load(dateInput.value);});
 generateAll.addEventListener("click",()=>{void generate();});
 manual.addEventListener("click",()=>showWebView("rph"));
 window.rphTodayLoad=()=>{void load(dateInput.value);};
 const workspace=document.getElementById("workspace"),todayView=document.getElementById("view-today");
 if(workspace&&!workspace.hidden&&todayView&&!todayView.hidden)void load(dateInput.value);
})();
