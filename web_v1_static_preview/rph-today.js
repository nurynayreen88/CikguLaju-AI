/* RPH Hari Ini: independent source-backed cascading dropdowns for every
 * teachable timetable slot. One Jana Bahan discovers resources for all
 * selections; a download remains per Lesson and uses the native Telegram
 * endpoint/quota. No guessed lesson, duplicate catalog or batch trial debit.
 */
(()=>{
 "use strict";
 const dateInput=document.getElementById("today-date");
 const weekSelect=document.getElementById("today-week");
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
 const dayMode=document.getElementById("rph-day-mode");
 const weekMode=document.getElementById("rph-week-mode");
 const bundlePanel=document.getElementById("week-bundle-panel");
 const bundleFormat=document.getElementById("week-bundle-format");
 const bundleDownload=document.getElementById("week-bundle-download");
 const bundleStatus=document.getElementById("week-bundle-status");
 const bundleQuota=document.getElementById("week-bundle-quota");
 if(!dateInput||!refresh||!state||!list||!confirm||!generateAll||
    !allStatus||!resultsHost||!resultsList)return;
 let requestId=0,loadedDate="",loading=false,reviewing=false,savingProgress=false,choices=[],batchEpoch=0;
 let weekly=false,weekSlotCount=null;
 const noPdpDates=new Set();
 const cache=new Map(),rosterCounts=new Map();
 const bundleParts=new Map(),bundleAttempts=new Map();
 let bundleBusy=false,bundleSlots=[],singleDownloads=0;
 const WORD_MIME="application/vnd.openxmlformats-officedocument.wordprocessingml.document";
 const DLP_REVIEW_OFFSET=100;
 const TAGS=["component","theme","unit","topic","lesson"];
 const SOURCE_NAMES={
  BM:"Unit",ENGLISH:"Unit / Topic",PI:"Bidang / Tajuk",
  MATH:"Bidang / Unit",MATH_DLP:"Unit",MATH_SJKC:"Unit",MATH_SJKT:"Unit",
  SCIENCE:"Tema / Unit",SCIENCE_DLP:"Unit",MORAL:"Unit / Nilai",
  PSV:"Bidang / Unit",PJPK:"Unit / Tajuk",ARAB:"Unit",
  MUZIK:"Unit / Tajuk",SEJARAH:"Unit",RBT:"Unit"
 };
 const TYPES=new Set(["textbook","workbook","audio"]);
 const englishBookView=/^https:\/\/online\.anyflip\.com\/(?:rmzft\/wwgq|hykyg\/rrpd)\/mobile\/index\.html\?pageIndex=[1-9][0-9]{0,2}$/;

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
 function lessonPickerLabel(code){
  return ["ENGLISH","SCIENCE_DLP","MATH_DLP"].includes(code)?"Lesson":"PdP";
 }
 function dlpReviewNumber(title,code,year){
  const byYear={2:{SCIENCE_DLP:4,MATH_DLP:18},3:{SCIENCE_DLP:4,MATH_DLP:9}};
  const limit=(byYear[year]||{SCIENCE_DLP:10,MATH_DLP:8})[code];
  const match=/^Review\s+([0-9]{2})\b/i.exec(title);
  const number=Number(match?.[1]);
  return number>=1&&number<=limit?number:null;
 }
 function nativeLessonLabel(item,code,year){
  let text=String(item.label||"").trim();
  if(!/^(?:PdP|Lesson)\s*0*[1-9][0-9]*/i.test(text)){
   const n=item.pdp_no??item.lesson_no??item.sequence_no;
   if(Number.isInteger(n)&&n>0&&n<10000)
    text=lessonPickerLabel(code)+" "+String(n).padStart(3,"0")+" — "+text;
  }
  const review=/^Review\s+[0-9]{2}\s+•\s+\S/.test(text)&&dlpReviewNumber(text,code,year)!==null;
  if(!review&&!/^(?:Lesson|PdP)\s*0*[1-9][0-9]*(?:\b|\s|[•—–:-])/i.test(text))return "";
  const book=String(item.textbook_ref||item.student_book_ref||"").trim();
  if(book&&!text.includes(book))text+=" • "+book;
  return text;
 }
 const summaryStatus=document.getElementById("pdp-summary-status");
 const summaryList=document.getElementById("pdp-summary-list");
 const summaryRetry=document.getElementById("pdp-summary-retry");
 let summaryRequest=0;

 async function loadProgressSummary(){
  if(!summaryList)return;
  const ticket=++summaryRequest;
  summaryRetry.hidden=true;
  summaryStatus.textContent="Memuatkan kemajuan PdP…";
  summaryList.replaceChildren();
  try{
   const response=await fetch("/api/web/rph/hari-ini/progress",{
    credentials:"same-origin",cache:"no-store",redirect:"error"
   });
   if(!response.ok)throw Error("Kemajuan PdP belum dapat disemak.");
   const {year,entries}=await response.json();
   if(ticket!==summaryRequest)return;
   if(!Number.isInteger(year)||!Array.isArray(entries))
    throw Error("Kemajuan PdP belum dapat disemak.");
   const classes=new Map();
   for(const row of entries){
    if(!classes.has(row.class_name))classes.set(row.class_name,[]);
    classes.get(row.class_name).push(row);
   }
   const content=document.createDocumentFragment();
   const dates=new Intl.DateTimeFormat("ms-MY",{
    timeZone:"Asia/Kuala_Lumpur",day:"numeric",month:"short"
   });
   for(const [name,rows] of classes){
    const heading=create("h4","",name);
    const subjects=create("ul","pdp-summary-subjects");
    for(const row of rows){
     const item=create("li");
     const latest=row.last_label||row.label+" "+row.last_number;
     const detail=row.completed
      ? row.completed+" "+row.label+" selesai · Terakhir: "+latest+" ("+dates.format(new Date(row.last_date+"T12:00:00+08:00"))+")"
      : "Belum ada rekod PdP";
     item.append(create("strong","",row.subject),create("span","notice",detail));
     subjects.append(item);
    }
    content.append(heading,subjects);
   }
   summaryList.replaceChildren(content);
   summaryStatus.textContent=entries.length?String(year):
    "Tambah waktu mengajar dalam Jadual Waktu untuk melihat kemajuan di sini.";
  }catch(_error){
   if(ticket!==summaryRequest)return;
   summaryStatus.textContent="Kemajuan PdP belum dapat disemak.";
   summaryRetry.hidden=false;
  }
 }

 function includedChoices(){
  return choices.filter(c=>!noPdpDates.has(c.date));
 }
 function updateAll(){
  const included=includedChoices();
  const selectable=included.filter(c=>c.slot.can_prepare);
  const materialsAllowed=canGenerateRph();
  confirmWrap.hidden=!included.length;
  if(weekSlotCount&&weekSlotCount.textContent!==String(included.length))
   weekSlotCount.textContent=String(included.length);
  for(const checkbox of list.querySelectorAll(".daily-rph-no-pdp")){
   checkbox.disabled=loading||reviewing||bundleBusy||Boolean(singleDownloads)||savingProgress;
  }
  const incomplete=selectable.filter(c=>!c.controls.lesson.value);
  const busy=selectable.some(c=>c.busy);
  // Keep the original all-slots guard, covered by existing RPH Hari Ini QA.
  generateAll.disabled=loading||reviewing||!confirm.checked||!selectable.length||!materialsAllowed||
   (weekly?busy||selectable.every(c=>!c.controls.lesson.value):
    selectable.some(c=>c.busy||!c.controls.lesson.value));
  for(const c of choices){
   for(const name of TAGS){
    const select=c.controls[name];
    if(select&&!select.hidden&&select.dataset.ready==="1")
     select.disabled=reviewing||!select.dataset.hasOptions;
   }
   if(c.progressHint)renderProgress(c);
  }
  // Inform teachers why batch generation is disabled without changing the
  // existing button, selection flow, or any generation/credit endpoints.
  // Only saved timetable slot labels and source-backed selection states appear.
  if(!loading&&!reviewing&&resultsHost.hidden){
   if(!materialsAllowed){
    allStatus.textContent=selectable.length?rphMaterialsAccessMessage():"";
    return;
   }
   const done=selectable.length-incomplete.length;
   if(weekly){
    const pending=included.length-selectable.length;
    allStatus.textContent=selectable.length
     ?done+" daripada "+selectable.length+" slot sudah dipilih. "+
      (done?(confirm.checked?"Tekan Sediakan RPH Minggu Ini.":"Sahkan hari PdP sebelum menyemak bahan."):
       "Pilih Lesson/PdP untuk slot yang hendak disediakan.")
     :"";
    if(pending)allStatus.textContent+=(selectable.length?" ":"")+pending+
     " slot belum ada RPH untuk muat turun gabungan.";
    return;
   }
   if(!selectable.length){
    allStatus.textContent=included.length
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
  bundleSlots=[];
  if(bundlePanel)bundlePanel.hidden=true;
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
 function lessonNumber(title,code,year){
  const review=dlpReviewNumber(title,code,year);
  if(review!==null)return DLP_REVIEW_OFFSET+review;
  const match=/^(?:Lesson|PdP)\s*(\d+)/i.exec(title);
  return match?Number(match[1]):null;
 }
 function selectedComponent(c){
  return c.controls.component.value||c.slot.component||"";
 }
 function suggestedLessonNumbers(c){
  if(!weekly)return c.slot.suggested_session||[];
  const component=selectedComponent(c);
  return c.slot.rpt_suggestion?.lessons?.[component]||[];
 }
 function renderWeeklySuggestion(c){
  const suggestion=c.slot.rpt_suggestion;
  if(!suggestion)return;
  const label=c.slot.subject_code==="ENGLISH"?"Lesson":"PdP";
  const numbers=suggestedLessonNumbers(c);
  const assigned=c.slot.suggested_session?.map(n=>String(n).padStart(3,"0")).join(" + ");
  if(!weekly){
   c.weeklySuggestion.textContent=assigned
    ?"Cadangan slot ini: "+label+" "+assigned+"."
    :"Pilih Lesson/PdP mengikut kemajuan kelas.";
   return;
  }
  const prefix="Cadangan RPT · Minggu "+suggestion.week+" (Kumpulan "+suggestion.group+")";
  const lessonLabels=suggestion.sessions
   ? suggestion.sessions.map(session=>session.map(n=>String(n).padStart(3,"0")).join(" + "))
   : numbers.map(n=>String(n).padStart(3,"0"));
  c.weeklySuggestion.textContent=numbers.length
   ? prefix+" — "+label+" "+lessonLabels.join(", ")
   : prefix+(c.slot.subject_code==="PJPK"&&!c.controls.component.value
      ? " — Pilih PJ atau PK untuk melihat cadangan."
      : " — Tiada "+label+" untuk pilihan ini.");
  const capacity=c.slot.rpt_capacity;
  if(capacity&&capacity.scheduled_minutes<capacity.required_minutes){
   c.weeklySuggestion.textContent+=suggestion.sessions
    ? ". Jadual kelas ada "+(capacity.scheduled_minutes/60)+" sesi 60 minit pada hari berbeza. "+
      "RPT memerlukan "+suggestion.sessions.length+" sesi minggu ini."
    : ". Jadual kelas ada "+capacity.scheduled_minutes+
      " minit minggu ini. RPT memerlukan "+capacity.required_minutes+" minit.";
  }
  if(assigned){
   c.weeklySuggestion.textContent+=" Cadangan slot ini: "+label+" "+assigned+".";
  }
 }
 function renderProgress(c){
  const component=selectedComponent(c);
  const progress=c.slot.progress?.[component];
  const label=c.slot.subject_code==="ENGLISH"?"Lesson":"PdP";
  const isDlp=["SCIENCE_DLP","MATH_DLP"].includes(c.slot.subject_code);
  const describe=number=>{
   if(isDlp){
    if(number>DLP_REVIEW_OFFSET)return "Review "+String(number-DLP_REVIEW_OFFSET).padStart(2,"0");
    return "Lesson "+String(number).padStart(2,"0");
   }
   return label+" "+String(number).padStart(3,"0");
  };
  const previous=progress?.previous;
  const completed=progress?.completed;
  const completedNumber=number=>c.slot.rpt_suggestion?.sessions
   ?.find(session=>session.includes(number))?.at(-1)??number;
  let next=!isDlp&&previous&&previous<999?previous+1:null;
  if(c.slot.subject_code==="SCIENCE"&&c.slot.year===6){
   if(previous===89)next=1;
   if(previous===84)next=null;
  }
  c.progressHint.textContent=completed
   ?describe(completed)+" selesai untuk slot ini."
   :previous?"Terakhir selesai "+describe(previous)+".":"";
  if(c.progressActions&&!c.progressActions.hidden&&!confirm.checked)
   c.progressHint.textContent+=(c.progressHint.textContent?" ":"")+"Sahkan hari PdP di atas untuk menyimpan rekod.";
  const selection=c.controls.lesson.selectedOptions[0];
  let nextAvailable=false;
  for(const option of c.controls.lesson.options){
   if(!option.dataset.lessonLabel)continue;
   const number=lessonNumber(option.dataset.lessonLabel,c.slot.subject_code,c.slot.year);
   if(number===next)nextAvailable=true;
   const badge=c.slot.suggested_session?.includes(number)?" · Cadangan slot ini":
     !completed&&number===next?" · Sambungan kelas":
     suggestedLessonNumbers(c).includes(number)?" · Cadangan minggu ini":"";
   const title=option.dataset.lessonLabel+badge;
   if(option.textContent!==title)option.textContent=title;
  }
  if(!completed&&nextAvailable)c.progressHint.textContent+=" Sambungan kelas: "+describe(next)+".";
  c.complete.hidden=Boolean(completed)&&
    (!selection?.dataset.completionToken||completedNumber(lessonNumber(selection.dataset.lessonLabel,c.slot.subject_code,c.slot.year))===completed);
  c.complete.textContent=completed?"Betulkan rekod PdP":"Selesai PdP";
  c.complete.disabled=savingProgress||reviewing||!confirm.checked||
    !selection?.dataset.completionToken||completedNumber(lessonNumber(selection.dataset.lessonLabel,c.slot.subject_code,c.slot.year))===completed;
  c.undoCompletion.hidden=!completed;
  c.undoCompletion.disabled=savingProgress||reviewing||!confirm.checked;
 }
 async function changeCompletion(c,undo=false){
  const button=undo?c.undoCompletion:c.complete;
  if(button.disabled||savingProgress||noPdpDates.has(c.date))return;
  const token=undo?null:c.controls.lesson.selectedOptions[0]?.dataset.completionToken;
  const body={date:loadedDate,start:c.slot.start,class_name:c.slot.class_name,
   subject_code:c.slot.subject_code,component:selectedComponent(c),token};
  savingProgress=true;
  c.progressStatus.textContent="Menyimpan rekod PdP…";
  updateAll();
  try{
   const response=await fetch("/api/web/rph/hari-ini/completion",{
    method:"POST",credentials:"same-origin",cache:"no-store",redirect:"error",
    headers:{"Content-Type":"application/json"},body:JSON.stringify(body)
   });
   const data=await response.json().catch(()=>({}));
   if(!response.ok||!Array.isArray(data.entries))throw Error(data.error||"Rekod PdP belum dapat disahkan.");
   if(document.getElementById("view-account")?.hidden===false)void loadProgressSummary();
   if(c.ticket!==requestId)return;
   for(const choice of choices){
    const fresh=data.entries.find(slot=>slot.start===choice.slot.start&&
      slot.class_name===choice.slot.class_name&&slot.subject_code===choice.slot.subject_code);
    if(fresh)choice.slot.progress=fresh.progress;
   }
   c.progressStatus.textContent=undo?"Tanda selesai dibatalkan.":"Rekod PdP disimpan.";
  }catch(error){
   if(c.ticket===requestId)c.progressStatus.textContent=error.message;
  }finally{savingProgress=false;updateAll();}
 }
 function fill(c,name,items,label){
  const select=c.controls[name];
  select.replaceChildren(new Option("Pilih "+label,""));
  for(const item of items){
   if(item.value==null||!item.label)continue;
   let title=String(item.label);
   if(name==="unit")title=nativeUnitLabel(title,c.slot.subject_code);
   if(name==="lesson"){
    title=nativeLessonLabel(item,c.slot.subject_code,c.slot.year);
    if(!title)continue;
   }
   const option=new Option(title,String(item.value));
   if(name==="lesson"){
     option.dataset.lessonLabel=title;
     option.dataset.completionToken=String(item.completion_token||"");
     if(c.slot.suggested_session?.includes(lessonNumber(title,c.slot.subject_code,c.slot.year)))
      option.textContent+=" · Cadangan slot ini";
     else if(!c.progressHint&&suggestedLessonNumbers(c).includes(lessonNumber(title,c.slot.subject_code,c.slot.year)))
      option.textContent+=" · Cadangan minggu ini";
     option.dataset.bookRef=String(item.textbook_ref||item.student_book_ref||"").trim();
     option.dataset.activityBookRef=String(item.activitybook_ref||"").trim();
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
  if(kind==="pdp"||kind==="bm-pdp")params.set("rph_today","1");
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
  c.reflectionMode.value="auto";
  c.reflectionManual.hidden=true;
  const code=c.slot.subject_code,control=c.controls;
  if(from==="lesson"){
   const chosen=control.lesson.selectedOptions[0];
   const references=[chosen?.dataset.bookRef,chosen?.dataset.activityBookRef].filter(Boolean).join(" • ");
   c.bookRef.textContent=references?"Rujukan buku: "+references:"";
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
  }else if(from==="component"){
   renderWeeklySuggestion(c);
   if(control.component.value)
    await loadStage(c,"unit","units",{subject:code,component:control.component.value},"Unit");
  }else if(from==="theme"&&control.theme.value){
   await loadStage(c,"unit","bm-units",{subject:"BM",theme:control.theme.value},"Unit");
  }else if(from==="unit"&&control.unit.value){
   if(code==="BM"){
    await loadStage(c,"topic","bm-topics",{subject:"BM",theme:control.theme.value,unit:control.unit.value},"Tajuk");
   }else{
    const extra={subject:code,unit:control.unit.value};
    if(code==="PJPK")extra.component=control.component.value;
    await loadStage(c,"lesson","pdp",extra,lessonPickerLabel(code));
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
   // The timetable has validated this DLP subject. Its native unit endpoint
   // verifies the catalogue directly, as in the standalone DLP picker.
   if(c.slot.curriculum==="dlp"){
    await advance(c,"subject");
    return;
   }
   const extra=["sjkc","sjkt"].includes(c.slot.curriculum)?{curriculum:c.slot.curriculum}:{};
   const items=await sourceOptions(c.slot.year,"subjects",extra);
   if(c.ticket!==requestId)return;
   if(!items.some(x=>x.value===c.slot.subject_code)){
    c.message.textContent="Subjek jadual belum tersedia dalam katalog sumber untuk Tahun "+c.slot.year+".";
    return;
   }
   await advance(c,"subject");
  }catch(error){if(c.ticket===requestId)c.message.textContent=error.message;}
  finally{c.busy=false;updateAll();}
 }
 function makeChoice(slot,index,ticket,progressEditable,parent,slotDate){
  const card=create("article","daily-rph-card");
  const heading=create("div","daily-rph-card-top");
  heading.append(create("strong","",slot.class_name+" · "+slot.subject),
                 create("span","daily-rph-time",slot.start+" – "+slot.end));
  card.append(heading);
  const subjectLabel=slot.subject_code==="ENGLISH"?"Bahasa Inggeris (SK)":slot.subject;
  const info=create("p","daily-rph-note",slot.year?"Tahun "+slot.year+" · "+subjectLabel:subjectLabel);
  card.append(info);
  const c={slot,index,ticket,date:slotDate,card,rev:0,busy:false,controls:{}};
  if(!slot.can_prepare){
   card.append(create("p","notice",slot.reason||"Waktu ini tidak mempunyai padanan sumber yang disahkan."));
   if(slot.rpt_subject){
    const rpt=create("button","","Buka RPT 2027");
    rpt.type="button";
    rpt.addEventListener("click",()=>void window.openScheduledRpt(slot.rpt_subject,slot.year));
    card.append(rpt);
   }
   parent.append(card);
   return c;
  }
  c.editor=create("div","daily-rph-editor");
  c.editor.append(create("h3","","Pilih Tajuk / Topik / Lesson"));
  if(slot.rpt_suggestion){
   c.weeklySuggestion=create("p","notice");
   c.weeklySuggestion.setAttribute("aria-live","polite");
   c.editor.append(c.weeklySuggestion);
  }
  c.message=create("p","notice");
  c.bookRef=create("p","notice");
  for(const [name,label] of [
   ["component","Komponen PJ atau PK"],["theme","Tema"],["unit",SOURCE_NAMES[slot.subject_code]||"Unit / Tajuk"],
   ["topic","Tajuk"],["lesson",lessonPickerLabel(slot.subject_code)]
  ])stage(c,name,label);
  renderWeeklySuggestion(c);
  if(slot.progress&&(progressEditable||Object.values(slot.progress).some(record=>record.previous))){
   c.progressHint=create("p","notice");
   c.progressStatus=create("p","notice");
   c.progressStatus.setAttribute("role","status");
   c.complete=create("button","","Selesai PdP");
   c.undoCompletion=create("button","secondary","Batal tanda selesai");
   c.complete.type=c.undoCompletion.type="button";
   c.complete.addEventListener("click",()=>{void changeCompletion(c);});
   c.undoCompletion.addEventListener("click",()=>{void changeCompletion(c,true);});
   c.progressActions=create("div","daily-rph-batch daily-rph-progress-actions");
   c.progressActions.hidden=!progressEditable;
   c.progressActions.append(c.complete,c.undoCompletion);
   c.editor.append(c.progressHint,c.progressActions,c.progressStatus);
  }
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
  const schoolYear=c.date.slice(0,4),rosterKey=schoolYear+"\n"+slot.class_name;
  if(!rosterCounts.has(rosterKey)){
   rosterCounts.set(rosterKey,readPbdRosterCount(slot.class_name,schoolYear).catch(()=>null));
  }
  void rosterCounts.get(rosterKey).then(count=>{
   if(ticket!==requestId)return;
   if(count)c.students.placeholder=String(count)+" daripada Rekod PBD";
   else countHint.textContent=count===0?"Senarai murid sesi "+schoolYear+" masih kosong. Guru boleh isi jumlah di sini.":
    "Rekod PBD belum dapat disemak. Guru boleh isi jumlah di sini.";
  });
  const reflectionPanel=create("div","rph-reflection");
  c.reflectionMode=create("select");
  c.reflectionMode.id="daily-rph-reflection-mode-"+index;
  c.reflectionMode.add(new Option("Auto (ikut RPH)","auto"));
  c.reflectionMode.add(new Option("Manual (tulis sendiri)","manual"));
  const reflectionModeLabel=create("label","","Refleksi");
  reflectionModeLabel.htmlFor=c.reflectionMode.id;
  c.reflectionManual=create("div");
  c.reflectionManual.hidden=true;
  c.reflectionMode.addEventListener("change",()=>{
   c.reflectionManual.hidden=c.reflectionMode.value!=="manual";
  });
  c.reflection=create("textarea");
  c.reflection.rows=3;
  c.reflection.maxLength=500;
  c.reflection.id="daily-rph-reflection-"+index;
  const reflectionLabel=create("label","","Catatan refleksi");
  reflectionLabel.htmlFor=c.reflection.id;
  const reflectionHint=create("p","notice","Maksimum 500 aksara dan 6 baris.");
  reflectionHint.id=c.reflection.id+"-hint";
  c.reflection.setAttribute("aria-describedby",reflectionHint.id);
  c.reflectionManual.append(reflectionLabel,c.reflection,reflectionHint);
  reflectionPanel.append(reflectionModeLabel,c.reflectionMode,c.reflectionManual);
  c.editor.append(c.bookRef,c.message,countLabel,c.students,countHint,reflectionPanel);
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
  parent.append(card);
  void initialize(c);
  return c;
 }
 function renderDaySlots(day,ticket,progressEditable){
  const caption=create("label","daily-rph-day-confirm");
  const checkbox=create("input","daily-rph-no-pdp");
  checkbox.type="checkbox";
  checkbox.checked=noPdpDates.has(day.date);
  caption.append(checkbox,create("span","","Tiada PdP pada "+day.day+", "+formatSlotDate(day.date)));
  const notice=create("p","notice","Slot hari ini dikecualikan sehingga halaman dimuat semula.");
  notice.setAttribute("role","status");
  const slots=create("div","daily-rph-day-slots");
  notice.hidden=!checkbox.checked;
  slots.hidden=checkbox.checked;
  if(day.entries.some(slot=>slot.can_prepare))list.append(caption,notice);
  list.append(slots);
  for(const slot of day.entries)
   choices.push(makeChoice(slot,choices.length,ticket,progressEditable,slots,day.date));
  checkbox.addEventListener("change",()=>{
   if(checkbox.checked)noPdpDates.add(day.date);
   else noPdpDates.delete(day.date);
   slots.hidden=checkbox.checked;
   notice.hidden=!checkbox.checked;
   confirm.checked=false;
   clearResults();
  });
 }
 function render(data,ticket){
  loadedDate=data.date;
  dateInput.value=data.date;
  confirm.checked=false;
  resultsHost.hidden=true;
  resultsList.replaceChildren();
  list.replaceChildren();
  choices=[];
  if(data.closure)list.append(create("p","notice",data.closure+". Tiada slot RPH untuk tarikh ini."));
  else if(!data.count)list.append(create("p","notice",
   "Tiada waktu mengajar pada "+data.day+". Pilih tarikh lain atau kemas kini Jadual Waktu di Profil Guru."));
  else renderDaySlots(data,ticket,data.progress_editable);
  state.textContent=data.day+", "+new Intl.DateTimeFormat("ms-MY",{
   timeZone:"Asia/Kuala_Lumpur",day:"numeric",month:"long",year:"numeric"
  }).format(new Date(data.date+"T12:00:00+08:00"))+
   (data.closure?". ":" · "+data.count+" waktu dalam jadual. ")+data.holiday_notice+
   (data.progress_unavailable?" Rekod PdP belum dapat disemak.":"");
  updateAll();
 }
 const weekDateFormatter=new Intl.DateTimeFormat("ms-MY",{
  timeZone:"Asia/Kuala_Lumpur",day:"numeric",month:"short",year:"numeric"
 });
 function formatSlotDate(value){
  return weekDateFormatter.format(new Date(value+"T12:00:00+08:00"));
 }
 function renderWeek(data,ticket){
  loadedDate=data.date;
  dateInput.value=data.date;
  if(weekSelect){
   const ranges=Array.isArray(data.weeks)?data.weeks:[{start:data.start,end:data.end,value:data.date}];
   weekSelect.replaceChildren(...ranges.map(range=>new Option(
    (range.current?"Minggu ini · ":"")+formatSlotDate(range.start)+" – "+formatSlotDate(range.end),
    range.value)));
   const shown=ranges.find(range=>range.start===data.start);
   if(shown)weekSelect.value=shown.value;
  }
  for(const day of data.days){
   if(!day.entries.length&&(!day.closure||day.closure==="Hujung minggu"))continue;
   list.append(create("h3","",day.day+" · "+formatSlotDate(day.date)));
   if(day.closure){
    list.append(create("p","notice",day.closure));
    continue;
   }
   renderDaySlots(day,ticket,false);
  }
  if(!data.count)list.append(create("p","notice",
   "Tiada waktu PdP minggu ini. Pilih tarikh lain atau semak Jadual Waktu di Profil Guru."));
  weekSlotCount=create("span");
  state.replaceChildren(formatSlotDate(data.start)+" hingga "+formatSlotDate(data.end)+" · ",
   weekSlotCount," slot PdP. "+data.holiday_notice+
   (data.progress_unavailable?" Rekod kemajuan kelas belum dapat disemak.":""));
  updateAll();
 }
 async function load(date=""){
  if(bundleBusy)return;
  const ticket=++requestId;
  cache.clear();
  rosterCounts.clear();
  if(bundlePanel)bundlePanel.hidden=true;
  bundleSlots=[];
  bundleParts.clear();
  bundleAttempts.clear();
  if(bundleQuota)bundleQuota.hidden=true;
  batchEpoch++;
  loading=true;reviewing=false;choices=[];weekSlotCount=null;
  resultsHost.hidden=true;
  resultsList.replaceChildren();
  list.replaceChildren();
  confirm.checked=false;confirmWrap.hidden=true;
  refresh.disabled=true;
  if(weekSelect)weekSelect.disabled=true;
  generateAll.disabled=true;
  allStatus.textContent="";
  state.textContent="Membaca jadual waktu daripada Profil Guru…";
  try{
   const qs=date?"?"+new URLSearchParams({date}):"";
   const endpoint=weekly?"/api/web/rph/minggu-ini":"/api/web/rph/hari-ini";
   const response=await fetch(endpoint+qs,{
    credentials:"same-origin",cache:"no-store",redirect:"error"
   });
   const data=await response.json().catch(()=>({}));
   if(ticket!==requestId)return;
   if(!response.ok)throw Error(data.error||"Jadual belum tersedia (HTTP "+response.status+").");
   if(typeof data.date!=="string"||(weekly?!Array.isArray(data.days):!Array.isArray(data.entries)))
    throw Error("Format jadual tidak sah.");
   if(weekly)renderWeek(data,ticket);
   else render(data,ticket);
  }catch(error){
   if(ticket!==requestId)return;
   choices=[];state.textContent=error.message;
  }finally{
   if(ticket===requestId){
    loading=false;refresh.disabled=false;
    if(weekSelect)weekSelect.disabled=!weekSelect.options.length;
    updateAll();
   }
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
 function selectedKey(c){return JSON.stringify({date:c.date,start:c.slot.start,...selection(c)});}
 function actionRow(name,action,url=null){
  const li=create("li","material-download-row");
  li.append(create("span","material-download-name",name));
  const button=create(url?"a":"button","material-download-action",action);
  if(url){
   button.href=url;
   button.rel="noopener";
   if(action!=="Muat Turun Audio")button.target="_blank";
  }
  li.append(button);
  return {li,button};
 }
 function readyMaterialLink(item,subject){
  if(!item||!TYPES.has(item.type)||typeof item.title!=="string"||
     typeof item.url!=="string"||!item.title.trim())return false;
  if(subject==="ENGLISH"&&/^\/api\/web\/rph\/english-paired-material\/(?:student-book|workbook|audio-[1-8])\?/.test(item.url))return true;
  if(subject==="ENGLISH"&&item.action==="Buka Buku Asal"&&englishBookView.test(item.url))return true;
  if(item.type==="workbook")return item.url.startsWith("/api/web/rph/english-workbook?");
  if(item.type==="textbook")return item.url.startsWith("/api/web/rph/english-student-book?")||
    (subject==="SCIENCE"&&item.url.startsWith("/api/web/rph/science-textbook?"));
  if(item.type==="audio")return (subject==="ENGLISH"&&/^\/api\/web\/rph\/english-audio\/[1-4]\?/.test(item.url))||
   (subject==="MUZIK"&&musicDownload(item));
  return false;
 }
 function musicDownload(item){
  return item.action==="Muat Turun Audio"&&
   /^https:\/\/drive\.usercontent\.google\.com\/download\?id=[A-Za-z0-9_-]{10,100}&export=download(?:&confirm=t)?$/.test(item.url);
 }
 async function inspectOne(c,epoch){
  const key=selectedKey(c),args=selection(c),qs=new URLSearchParams(args);
  if(c.slot.subject_code==="ENGLISH"){
   qs.set("rph_context","hari-ini");
   qs.set("teacher_date",c.date);
   qs.set("teacher_start",c.slot.start);
   qs.set("teacher_end",c.slot.end);
  }
  c.result.hidden=false;c.resultList.replaceChildren();
  c.downloadFormats=[];
  c.downloadStatus.textContent="Menyemak bahan yang tersedia…";
  let found=0, errors=[], paired=false;
  try{
   const availability=await fetch("/api/web/rph/availability?"+qs,{
    credentials:"same-origin",cache:"no-store",redirect:"error"
   });
   const data=await availability.json().catch(()=>({}));
   if(epoch!==batchEpoch||key!==selectedKey(c))return;
   if(updateRphTrialFromDenial(data))return;
   paired=data.code==="TELEGRAM_ENGLISH_INTEGRATED_UNAVAILABLE";
   if(availability.ok&&data.available===true&&data.generator==="telegram-native"){
    const pair=Array.isArray(data.lessons)?data.lessons.map(n=>String(n).padStart(3,"0")).join(" + "):"";
    paired=Boolean(pair);
    const pbd=actionRow("Pentaksiran Bilik Darjah","Rekod PBD");
    pbd.button.addEventListener("click",()=>window.cikgulajuPbdFromRph?.({
      className:c.slot.class_name,date:c.date,subject:c.slot.subject,
      lesson:pair?"Lesson "+pair:c.controls.lesson.selectedOptions[0]?.textContent||""
    },Object.fromEntries(qs)));
    c.resultList.append(pbd.li);found++;
    const formats=Array.isArray(data.formats)?data.formats.filter(f=>["pdf","word"].includes(f)):["pdf","word"];
    c.downloadFormats=formats;
    for(const format of ["pdf","word"]){
     if(!formats.includes(format))continue;
     const label=(format==="pdf"?"RPH PDF":"RPH Word")+(pair?" · Lesson "+pair:"");
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
      c.slot.subject_code==="MUZIK"||(c.slot.subject_code==="SCIENCE"&&[1,2,3,5,6].includes(c.slot.year))){
   try{
    const params=new URLSearchParams({year:args.year,subject:args.subject,unit:args.unit,lesson:args.lesson});
    if(paired)params.set("paired","1");
    const response=await fetch("/api/web/rph/extra-materials?"+params,{
      credentials:"same-origin",cache:"no-store",redirect:"error"
    });
    const data=await response.json().catch(()=>({}));
    if(epoch!==batchEpoch||key!==selectedKey(c))return;
    if(updateRphTrialFromDenial(data))return;
    if(response.ok&&Array.isArray(data.items)&&data.items.length<=30){
     if(typeof data.pair_note==="string")errors.push(data.pair_note);
     for(const item of data.items){
      if(c.slot.subject_code==="SCIENCE"&&item?.action==="local-pdf"){
       const copy=window.cikgulajuPdpPdfCopy?.(item,c.downloadStatus);
       if(copy){
        const row=actionRow(item.title,"Pilih PDF Asal");
        row.button.addEventListener("click",copy);
        c.resultList.append(row.li);found++;
       }
       continue;
      }
      if(!readyMaterialLink(item,c.slot.subject_code))continue;
      const label=item.title;
      const action=item.type==="audio"?"Muat Turun Audio":englishBookView.test(item.url)?"Buka Buku Asal":"Download";
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
 function rphFileRequest(c,format){
  const students=c.students.value.trim();
  if(!c.students.checkValidity()||(students&&!/^[1-9][0-9]{0,2}$/.test(students))){
   c.students.reportValidity();
   throw Error("Masukkan bilangan murid antara 1 hingga 200 untuk "+c.slot.class_name+".");
  }
  const args=selection(c);
  const params=new URLSearchParams({
   year:args.year,subject:args.subject,unit:args.unit,lesson:args.lesson,
   teacher_class:c.slot.class_name,teacher_date:c.date,
   teacher_start:c.slot.start,teacher_end:c.slot.end,teacher_students:students,
   rph_context:"hari-ini"
  });
  if(args.component)params.set("component",args.component);
  const query=params.toString(),options=rphDownloadOptions(c.reflectionMode.value,c.reflection.value,c.slot.class_name);
  const key=JSON.stringify([format,query,options.body||""]);
  const safeClass=c.slot.class_name.replace(/[^a-z0-9_-]+/gi,"_").slice(0,45);
  const fallback="CIKGULAJU_RPH_"+safeClass+"_"+args.subject+"_"+format+"."+(format==="pdf"?"pdf":"docx");
  return {c,format,query,options,key,fallback};
 }
 function saveRphFile(blob,name){
  const url=URL.createObjectURL(blob),anchor=document.createElement("a");
  anchor.href=url;anchor.download=name;
  document.body.append(anchor);anchor.click();anchor.remove();
  setTimeout(()=>URL.revokeObjectURL(url),30000);
 }
 async function fetchRphPart({format,query,options,fallback}){
  const response=await fetch("/api/web/rph/"+format+"?"+query,options);
  if(!response.ok){
   const body=await response.json().catch(()=>({}));
   updateRphTrialFromDenial(body);
   throw Error(body.error||"Muat turun RPH gagal (HTTP "+response.status+").");
  }
  const mime=(response.headers.get("content-type")||"").toLowerCase();
  const blob=await response.blob();
  if(!mime.includes(format==="pdf"?"application/pdf":WORD_MIME)||blob.size<1000)
   throw Error("Fail RPH yang diterima tidak sah.");
  const name=response.headers.get("Content-Disposition")?.match(/filename="?([A-Za-z0-9_-]+\.(?:pdf|docx))"?/i)?.[1];
  return {blob,name:name||fallback,receipt:response.headers.get(
   format==="pdf"?"X-RPH-PDF-Receipt":"X-RPH-Word-Receipt")};
 }
 async function downloadRph(c,format,key,button){
  if(c.ticket!==requestId||reviewing||bundleBusy||key!==selectedKey(c)||!confirm.checked||
     noPdpDates.has(c.date))return;
  singleDownloads++;
  button.disabled=true;
  updateAll();
  updateBundle();
  try{
   const plan=rphFileRequest(c,format);
   c.downloadStatus.textContent="Menyediakan RPH "+format.toUpperCase()+"…";
   const part=bundleParts.get(plan.key)||await fetchRphPart(plan);
   if(c.ticket!==requestId||key!==selectedKey(c))
    throw Error("Pilihan Lesson telah berubah. Semak semula sebelum muat turun.");
   saveRphFile(part.blob,part.name);
   c.downloadStatus.textContent="RPH "+format.toUpperCase()+" disediakan untuk "+c.slot.class_name+".";
   window.refreshSharedRphBalance?.();
  }catch(error){c.downloadStatus.textContent=error.message;}
  finally{button.disabled=false;singleDownloads--;updateAll();updateBundle();}
 }
 function updateBundle(){
  if(!bundlePanel)return;
  bundlePanel.hidden=!weekly||resultsHost.hidden||!bundleSlots.length;
  if(bundlePanel.hidden)return;
  for(const option of bundleFormat.options){
   option.disabled=!bundleSlots.every(c=>c.downloadFormats?.includes(option.value));
  }
  if(bundleFormat.selectedOptions[0]?.disabled){
   const available=[...bundleFormat.options].find(option=>!option.disabled);
   if(available)bundleFormat.value=available.value;
  }
  const supported=Boolean(bundleFormat.selectedOptions[0]&&!bundleFormat.selectedOptions[0].disabled);
  bundleFormat.disabled=bundleBusy||!supported;
  bundleDownload.disabled=bundleBusy||Boolean(singleDownloads)||reviewing||!confirm.checked||!supported;
  if(!supported)
   bundleStatus.textContent="Pilih slot yang semuanya mempunyai format RPH yang sama untuk digabungkan.";
 }
 function showBundleQuota(data){
  if(!bundleQuota)return;
  if(data.access_mode==="partner"){
   bundleQuota.textContent="Rakan Pembangun · Tanpa had";
  }else if(data.access_mode==="subscription"&&Number.isInteger(data.remaining)
           &&data.usage_week_start&&data.usage_week_end){
   bundleQuota.textContent="Baki muat turun mingguan "+data.remaining+" daripada 2 · "+
    formatSlotDate(data.usage_week_start)+" – "+formatSlotDate(data.usage_week_end);
  }else{
   bundleQuota.hidden=true;
   return;
  }
  bundleQuota.hidden=false;
 }
 async function combineWeeklyFiles(parts,format,exportId){
  const form=new FormData();
  for(const {blob,receipt,name} of parts){
   if(!receipt)throw Error("Pengesahan fail belum tersedia bagi salah satu slot.");
   form.append("document",blob,name);
   form.append("receipt",receipt);
  }
  const response=await fetch("/api/web/rph/timetable/"+format+"-bundle",{
   method:"POST",body:form,headers:{"X-RPH-Weekly-Export":exportId},
   credentials:"same-origin",cache:"no-store",redirect:"error"});
  if(!response.ok){
   const error=await response.json().catch(()=>({}));
   if(error.code==="RPH_WEEKLY_LIMIT")showBundleQuota(error);
   throw Error(error.error||"Gabungan RPH belum berjaya.");
  }
  const blob=await response.blob();
  const mime=format==="pdf"?"application/pdf":WORD_MIME;
  if(!blob.type.includes(mime)||blob.size<1000)throw Error("Fail gabungan RPH tidak sah.");
  const remaining=response.headers.get("X-RPH-Weekly-Remaining");
  if(remaining!==null)showBundleQuota({
   access_mode:"subscription",remaining:Number(remaining),
   usage_week_start:response.headers.get("X-RPH-Weekly-Start"),
   usage_week_end:response.headers.get("X-RPH-Weekly-End"),
  });
  return blob;
 }
 async function downloadBundle(){
  if(bundleDownload.disabled)return;
  const format=bundleFormat.value;
  let plans;
  try{
   plans=bundleSlots.map(c=>rphFileRequest(c,format));
  }catch(error){bundleStatus.textContent=error.message;return;}
  bundleBusy=true;
  updateAll();
  updateBundle();
  const lock=[dateInput,weekSelect,refresh,confirm,dayMode,weekMode,generateAll,manual,
   ...choices.flatMap(c=>c.editor?[...c.editor.querySelectorAll("select,input,textarea")]:[])]
   .filter(control=>control&&!control.disabled);
  for(const control of lock)control.disabled=true;
  let ready=plans.filter(plan=>bundleParts.has(plan.key)).length;
  try{
   const key=JSON.stringify(plans.map(plan=>plan.key));
   let exportId=bundleAttempts.get(key);
   if(!exportId){
    bundleStatus.textContent="Menyemak baki muat turun mingguan…";
    const response=await fetch("/api/web/rph/timetable/"+format+"-bundle",{
     credentials:"same-origin",cache:"no-store",redirect:"error"});
    const data=await response.json().catch(()=>({}));
    if(!response.ok)throw Error(data.error||"Gabungan RPH belum tersedia.");
    showBundleQuota(data);
    if(data.available!==true)throw Error("Had dua muat turun RPH mingguan telah dicapai.");
    exportId=crypto.randomUUID();
   }
   const missing=plans.length-ready;
   if(missing){
    bundleStatus.textContent="Menyemak akses untuk "+missing+" slot…";
    const account=await window.refreshSharedRphBalance();
    if(!account)throw Error("Baki janaan belum dapat disemak. Cuba semula.");
    if(account.rph_access_mode!=="paid"){
     const balance=account.rph_trial_remaining;
     if(!Number.isInteger(balance))throw Error("Baki janaan belum dapat disahkan.");
     if(balance<missing)throw Error("Gabungan ini memerlukan "+missing+
      " janaan. Baki semasa ialah "+balance+".");
    }
   }
   const parts=[];
   for(const plan of plans){
    let part=bundleParts.get(plan.key);
    if(!part){
     bundleStatus.textContent="RPH siap "+ready+"/"+plans.length+" · Menyediakan "+plan.c.slot.class_name+"…";
     try{part=await fetchRphPart(plan);}
     catch(error){throw Error(plan.c.slot.class_name+" ("+plan.c.slot.subject+"): "+error.message);}
     bundleParts.set(plan.key,part);
     ready++;
    }
    parts.push(part);
   }
   bundleStatus.textContent="Menggabungkan "+ready+" RPH dalam satu fail…";
   // Keep the same reference if the response is lost after the server counts the export.
   bundleAttempts.set(key,exportId);
   const blob=await combineWeeklyFiles(parts,format,exportId);
   bundleAttempts.delete(key);
   if(!confirm.checked||bundlePanel.hidden)return;
   saveRphFile(blob,"CIKGULAJU_RPH_MINGGU_INI_"+loadedDate+(format==="pdf"?".pdf":".docx"));
   bundleStatus.textContent=ready+" RPH disusun dalam satu fail "+(format==="pdf"?"PDF":"Word")+".";
  }catch(error){
   bundleStatus.textContent=error.message+
    (ready?" "+ready+" RPH sudah disimpan dalam tab ini untuk percubaan semula.":"");
  }finally{
   bundleBusy=false;
   for(const control of lock)control.disabled=false;
   updateAll();
   updateBundle();
   void window.refreshSharedRphBalance?.();
  }
 }
 async function generate(){
  if(generateAll.disabled)return;
  const selected=includedChoices().filter(c=>c.slot.can_prepare&&(!weekly||c.controls.lesson.value));
  if(!selected.length||selected.some(c=>!c.controls.lesson.value))return;
  reviewing=true;generateAll.disabled=true;updateAll();
  const epoch=++batchEpoch;
  // Keep the same chronological subject/class ordering as the upper cards.
  // Output is one grouped section beneath all subject selectors, not inline.
  resultsList.replaceChildren();
  let previousDate="";
  for(const c of selected){
   if(weekly&&c.date!==previousDate){
    resultsList.append(create("h4","",c.slot.day+" · "+formatSlotDate(c.date)));
    previousDate=c.date;
   }
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
    bundleSlots=weekly?selected:[];
    if(bundleStatus)bundleStatus.textContent="";
    updateBundle();
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
 function setWeekMode(next){
  if(weekly===next||bundleBusy)return;
  weekly=next;
  document.getElementById("today-date-wrap").hidden=weekly;
  document.getElementById("today-week-wrap").hidden=!weekly;
  dayMode.setAttribute("aria-pressed",String(!weekly));
  weekMode.setAttribute("aria-pressed",String(weekly));
  dayMode.classList.toggle("secondary",weekly);
  weekMode.classList.toggle("secondary",!weekly);
  document.getElementById("today-instructions").textContent=weekly
   ?"Tandakan Tiada PdP jika sekolah membatalkan kelas sepanjang hari. Pilih Lesson/PdP bagi slot yang hendak disediakan."
   :"RPH Hari Ini menunjukkan cadangan daripada RPH Minggu Ini untuk tarikh yang dipilih. Semak Lesson/PdP mengikut kemajuan kelas, kemudian catat Selesai PdP selepas mengajar.";
  document.getElementById("today-confirm-label").textContent=weekly
   ?"Saya sahkan slot yang dipilih berlangsung pada hari PdP."
   :"Saya sahkan tarikh ini hari PdP sebenar.";
  document.getElementById("today-generate-hint").textContent=weekly
   ?"Bahan disediakan untuk slot yang sudah dipilih."
   :"Pilih Lesson/PdP untuk semua kelas terlebih dahulu.";
  document.getElementById("today-results-heading").textContent=weekly?"Bahan RPH Minggu Ini":"Bahan RPH Hari Ini";
  generateAll.textContent=weekly?"Sediakan RPH Minggu Ini":"Jana Bahan Semua Lesson";
  list.setAttribute("aria-label",weekly?"Senarai waktu mengajar minggu ini":"Senarai waktu mengajar hari ini");
  void load(dateInput.value);
 }
 dayMode?.addEventListener("click",()=>setWeekMode(false));
 weekMode?.addEventListener("click",()=>setWeekMode(true));
 bundleFormat?.addEventListener("change",()=>{bundleStatus.textContent="";updateBundle();});
 bundleDownload?.addEventListener("click",()=>{void downloadBundle();});
 refresh.addEventListener("click",()=>{void load(dateInput.value);});
 dateInput.addEventListener("change",()=>{void load(dateInput.value);});
 weekSelect?.addEventListener("change",()=>{void load(weekSelect.value);});
 generateAll.addEventListener("click",()=>{void generate();});
 manual.addEventListener("click",()=>showWebView("rph"));
 summaryRetry?.addEventListener("click",()=>{void loadProgressSummary();});
 document.getElementById("profile-refresh")?.addEventListener("click",()=>{void loadProgressSummary();});
 document.getElementById("pdp-summary-today")?.addEventListener("click",()=>{
  showWebView("today");
  window.rphTodayLoad();
  document.getElementById("view-today-heading").focus();
 });
 document.getElementById("today-profile-progress")?.addEventListener("click",()=>{
  showWebView("account");
  document.getElementById("pdp-summary-heading").focus();
 });
 window.rphTodayLoad=()=>{void load(dateInput.value);};
 window.cikgulajuProgressLoad=loadProgressSummary;
 window.cikgulajuRphMaterialAccessChanged=()=>{
  if(canGenerateRph()){updateAll();return;}
  reviewing=false;
  clearResults();
 };
 const workspace=document.getElementById("workspace"),todayView=document.getElementById("view-today");
 if(workspace&&!workspace.hidden&&todayView&&!todayView.hidden)void load(dateInput.value);
})();
