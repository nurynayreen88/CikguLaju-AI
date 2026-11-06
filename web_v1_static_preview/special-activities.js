"use strict";
/* RPH Aktiviti Khas (DRAF): independently selected and sourced from Telegram.
   Never reinterpret a special activity as a syllabus Lesson, Unit or RPT week. */
(() => {
 const by=id=>document.getElementById(id);
 const kind=by("special-kind"), year=by("special-year");
 const phase=by("special-phase"), subject=by("special-subject");
 const activity=by("special-activity"), status=by("special-status");
 const action=by("special-show"), materials=by("special-materials");
 const list=by("special-materials-list"), note=by("special-materials-note");
 const teacherClass=by("special-class"), teacherDate=by("special-date");
 const start=by("special-start"), end=by("special-end"), students=by("special-students");
 let digest="", serial=0, downloadable=false, viewing=false;

 function optionList(el,values,label){
  el.replaceChildren(new Option(label,""));
  for(const x of values){
   if(!x || typeof x.label!=="string" || typeof x.value!=="string")continue;
   el.add(new Option(x.label,x.value));
  }
  el.disabled=el.options.length<=1;
 }
 function show(el,visible){el.hidden=!visible;}
 function setStatus(message){status.textContent=message;}
 function resetMaterials(){
  materials.hidden=true;list.replaceChildren();action.disabled=true;
  downloadable=false;note.textContent="";
 }
 function resetBelow(kindOfChange){
  serial++;
  digest="";
  resetMaterials();
  if(kindOfChange==="kind"){
   optionList(year,[1,2,3,4,5,6].filter(n=>kind.value!=="TRANSISI_TAHUN_1"||n===1).map(n=>({
    value:String(n),label:"Tahun "+n
   })),"Pilih Tahun");
   year.disabled=!kind.value;
  }
  if(["kind","year"].includes(kindOfChange)){
   optionList(subject,[],"Pilih Subjek");
   optionList(phase,[],"Pilih Fasa");
  }
  optionList(activity,[],"Pilih Aktiviti");
  show(by("special-subject-wrap"),kind.value==="SELEPAS_TAMAT_SUKATAN" && !!year.value);
  show(by("special-phase-wrap"),kind.value==="TRANSISI_TAHUN_1" && !!year.value);
  show(by("special-activity-wrap"),false);
  if(kind.value&&year.value)setStatus("Pilih subjek atau fasa untuk melihat aktiviti.");
  else setStatus("Pilih jenis aktiviti dan Tahun.");
 }

 function params(includeTeacher=false){
  const p=new URLSearchParams({kind:kind.value,year:year.value});
  if(kind.value==="TRANSISI_TAHUN_1")p.set("phase",phase.value);
  else p.set("subject",subject.value);
  if(includeTeacher){
   p.set("activity_id",activity.value);p.set("source_digest",digest);
   p.set("teacher_class",teacherClass.value.trim());
   p.set("teacher_date",teacherDate.value);
   p.set("teacher_start",start.value);p.set("teacher_end",end.value);
   p.set("teacher_students",students.value.trim());
  }
  return p;
 }
 async function apiGet(url){
  const r=await fetch(url,{credentials:"same-origin",cache:"no-store",redirect:"error"});
  const data=await r.json().catch(()=>({}));
  if(!r.ok)throw Error(data.error||"Sumber RPH Aktiviti Khas belum tersedia.");
  if(!data||typeof data!=="object")throw Error("Respons sumber tidak sah.");
  return data;
 }
 function populateClassHints(){
  const hints=by("special-class-hints");
  hints.replaceChildren();
  const fromProfile=document.getElementById("profile-classes")?.value||"";
  const entries=fromProfile.split(/\n/).map(x=>x.trim()).filter(Boolean);
  for(const name of [...new Set(entries)]){
   if(name.length>40)continue;
   const option=document.createElement("option");option.value=name;
   hints.append(option);
  }
 }
 async function fetchSubjects(){
  const seq=++serial;
  optionList(subject,[],"Memuatkan subjek…");
  optionList(activity,[],"Pilih Aktiviti");
  resetMaterials();
  setStatus("Menyemak pilihan subjek pada sumber Telegram…");
  try{
   const p=new URLSearchParams({kind:kind.value,year:year.value});
   const data=await apiGet("/api/web/aktiviti-khas/subjects?"+p);
   if(seq!==serial)return;
   if(!Array.isArray(data.items)||data.status!=="DRAF")throw Error("Sumber belum disahkan.");
   optionList(subject,data.items,"Pilih Subjek");
   setStatus("Pilih Subjek untuk memaparkan aktiviti tamat sukatan.");
  }catch(e){
   if(seq===serial)setStatus(e.message);
  }
 }
 async function fetchActivities(){
  const seq=++serial;
  resetMaterials();
  optionList(activity,[],"Memuatkan aktiviti…");
  show(by("special-activity-wrap"),false);
  setStatus("Memuatkan aktiviti sebenar dari sumber Telegram…");
  try{
   const data=await apiGet("/api/web/aktiviti-khas/options?"+params());
   if(seq!==serial)return;
   if(data.status!=="DRAF"||!/^[a-f0-9]{64}$/.test(String(data.source_digest||""))||
      !Array.isArray(data.items))throw Error("Sumber aktiviti tidak sepadan.");
   digest=data.source_digest;
   optionList(activity,data.items.map(x=>({value:x.id,label:x.label})),"Pilih Aktiviti");
   show(by("special-activity-wrap"),true);
   setStatus("Bahan tersedia sebagai DRAF untuk semakan. Pilih aktiviti.");
  }catch(e){
   if(seq===serial)setStatus(e.message);
  }
 }

 function validTeacher(){
  const cls=teacherClass.value.trim(), total=students.value.trim();
  if(cls.length>40 || (cls && !/^[\p{L}\p{N}_ .\-/()]+$/u.test(cls)))return "Nama kelas tidak sah.";
  if((start.value||end.value)&&(!start.value||!end.value||start.value>=end.value))
   return "Masukkan waktu mula dan tamat yang sah.";
  if(total&&(!/^[1-9][0-9]{0,2}$/.test(total)||Number(total)>200))
   return "Bilangan murid mesti 1–200.";
  return "";
 }
 function updateShow(){
  resetMaterials();
  action.disabled=!digest||!activity.value;
  if(activity.value)
   setStatus("Aktiviti dipilih. Tekan Papar Bahan untuk RPH Word/PDF.");
 }
 function filenameFromResponse(response,fmt){
  const contentDisposition=response.headers.get("Content-Disposition")||"";
  const match=/filename="?([A-Za-z0-9_.-]{1,150})"?/i.exec(contentDisposition);
  return match?match[1]:"CIKGULAJU_AKTIVITI_KHAS_"+activity.value+"_DRAF."+(fmt==="word"?"docx":"pdf");
 }
 async function download(fmt,button){
  if(!downloadable||viewing)return;
  const problem=validTeacher();
  if(problem){note.textContent=problem;return;}
  const requestDigest=digest;
  const requestActivity=activity.value;
  const current=serial;
  button.disabled=true;note.textContent="Menjana RPH "+fmt.toUpperCase()+" melalui Telegram…";
  try{
   const response=await fetch("/api/web/aktiviti-khas/"+fmt+"?"+params(true),{
    credentials:"same-origin",cache:"no-store",redirect:"error"
   });
   if(!response.ok){
    const data=await response.json().catch(()=>({}));
    throw Error(data.error||"Muat turun RPH gagal (HTTP "+response.status+").");
   }
   const contentType=(response.headers.get("Content-Type")||"").toLowerCase();
   if(fmt==="pdf"&&!contentType.includes("application/pdf"))throw Error("PDF tidak sah.");
   if(fmt==="word"&&!contentType.includes("wordprocessingml.document"))throw Error("Word tidak sah.");
   const file=await response.blob();
   if(!file.size||current!==serial||requestDigest!==digest||requestActivity!==activity.value)return;
   const fileUrl=URL.createObjectURL(file);
   try{
    const a=document.createElement("a");
    a.href=fileUrl;a.download=filenameFromResponse(response,fmt);
    document.body.append(a);a.click();a.remove();
   }finally{setTimeout(()=>URL.revokeObjectURL(fileUrl),120000);}
   const balance=response.headers.get("X-RPH-Trial-Remaining");
   note.textContent="RPH "+fmt.toUpperCase()+" DRAF berjaya dijana."+
    (balance!==null?" Baki janaan percuma: "+balance+".":"");
   if(typeof refreshSharedRphBalance==="function")
    void refreshSharedRphBalance();
  }catch(e){
   if(current===serial)note.textContent=e.message;
  }finally{button.disabled=false;}
 }
 function renderMaterials(){
  list.replaceChildren();
  const label=activity.selectedOptions[0]?.textContent||"Aktiviti";
  const title=document.createElement("li");
  title.textContent=label;
  title.style.fontWeight="700";
  list.append(title);
  for(const fmt of ["pdf","word"]){
   const row=document.createElement("li");row.className="material-download-row";
   const name=document.createElement("span");name.className="material-download-name";
   name.textContent="RPH "+(fmt==="pdf"?"PDF":"Word")+" (DRAF)";
   const btn=document.createElement("button");btn.type="button";
   btn.className="material-download-action";btn.textContent="Download";
   btn.addEventListener("click",()=>{void download(fmt,btn);});
   row.append(name,btn);list.append(row);
  }
  materials.hidden=false;downloadable=true;
  note.textContent="RPH Aktiviti Khas ialah DRAF tanpa SK/SP rasmi. Muat turun menggunakan akses Rakan Pembangun/langganan atau baki 10 janaan yang sama seperti Telegram.";
 }
 kind.addEventListener("change",()=>{resetBelow("kind");});
 year.addEventListener("change",()=>{
  resetBelow("year");
  if(!year.value)return;
  if(kind.value==="SELEPAS_TAMAT_SUKATAN")void fetchSubjects();
  else{
   optionList(phase,[
    {value:"Fasa Penyesuaian",label:"Fasa Penyesuaian"},
    {value:"Fasa Kesediaan",label:"Fasa Kesediaan"}
   ],"Pilih Fasa");
  }
 });
 phase.addEventListener("change",()=>{resetBelow("phase");if(phase.value)void fetchActivities();});
 subject.addEventListener("change",()=>{resetBelow("subject");if(subject.value)void fetchActivities();});
 activity.addEventListener("change",updateShow);
 action.addEventListener("click",()=>{
  if(!action.disabled){
   const issue=validTeacher();
   if(issue){setStatus(issue);return;}
   renderMaterials();
   action.disabled=true;
  }
 });
 document.querySelector('[data-web-view="special"]')?.addEventListener("click",populateClassHints);
 resetBelow("kind");
})();
