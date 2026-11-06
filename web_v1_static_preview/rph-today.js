/* CikguLaju RPH Hari Ini — authenticated, read-only schedule-first entry.
 * Each daily slot opens the *existing* verified native RPH flow. Lesson/PdP
 * must be confirmed, and generation uses the original quota/payment gates.
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
 let loading=false, requestId=0, rows=[], loadedDate="";
 if(!dateInput||!refresh||!state||!list||!confirm)return;

 function create(tag,cls,value){
  const el=document.createElement(tag);
  if(cls)el.className=cls;
  if(value!==undefined)el.textContent=String(value);
  return el;
 }
 function refreshButtons(){
  for(const btn of list.querySelectorAll("button[data-daily-index]")){
   const row=rows[Number(btn.dataset.dailyIndex)];
   btn.disabled=!row||!row.can_prepare||!confirm.checked||loading;
  }
 }
 function render(data){
  rows=data.entries;
  loadedDate=data.date;
  dateInput.value=data.date;
  confirm.checked=false;
  confirmWrap.hidden=!data.count;
  list.replaceChildren();
  if(!data.count){
   list.append(create("p","notice","Tiada waktu mengajar dalam jadual untuk "+data.day+". Anda boleh memilih tarikh lain atau kemas kini jadual di Profil Guru."));
  }
  for(const [i,slot] of rows.entries()){
   const card=create("article","daily-rph-card");
   const line=create("div","daily-rph-card-top");
   line.append(create("strong","",slot.class_name+" · "+slot.subject));
   line.append(create("span","daily-rph-time",slot.start+" – "+slot.end));
   card.append(line);
   const note=slot.can_prepare?
     "Tahun "+slot.year+" · "+(slot.subject_code==="PJPK"?
          (slot.component==="PJ"?"Pendidikan Jasmani":slot.component==="PK"?"Pendidikan Kesihatan":"Pilih komponen PJ atau PK"):
          slot.subject)+" · Lesson/PdP belum dipilih":
     (slot.reason||"Jadual ini belum boleh dipadankan.");
   card.append(create("p","daily-rph-note",note));
   const btn=create("button","daily-rph-prepare","Pilih Lesson/PdP");
   btn.type="button";
   btn.dataset.dailyIndex=String(i);
   btn.disabled=true;
   btn.addEventListener("click",async()=>{
    if(!confirm.checked||!slot.can_prepare||loading)return;
    btn.disabled=true;
    try{
     await window.prepareRphFromToday(slot,loadedDate);
    }catch(error){
     state.textContent="Pilihan jadual belum dapat disambungkan: "+error.message;
    }finally{
     refreshButtons();
    }
   });
   card.append(btn);
   list.append(card);
  }
  state.textContent=data.day+", "+new Intl.DateTimeFormat("ms-MY",{
   timeZone:"Asia/Kuala_Lumpur",day:"numeric",month:"long",year:"numeric"
  }).format(new Date(data.date+"T12:00:00+08:00"))+
   " · "+data.count+" waktu dalam jadual. "+data.holiday_notice;
  refreshButtons();
 }
 async function load(date=""){
  const ticket=++requestId;
  loading=true;
  list.replaceChildren();
  state.textContent="Membaca jadual waktu daripada Profil Guru…";
  confirm.checked=false;
  confirmWrap.hidden=true;
  refresh.disabled=true;
  try{
   const params=date?"?"+new URLSearchParams({date}):"";
   const res=await fetch("/api/web/rph/hari-ini"+params,{
    credentials:"same-origin",cache:"no-store",redirect:"error"
   });
   const data=await res.json().catch(()=>({}));
   if(ticket!==requestId)return;
   if(!res.ok)throw Error(data.error||"Jadual belum tersedia (HTTP "+res.status+").");
   if(!Array.isArray(data.entries)||typeof data.date!=="string")throw Error("Data jadual tidak sah.");
   render(data);
  }catch(e){
   if(ticket!==requestId)return;
   rows=[];
   list.replaceChildren();
   state.textContent=e.message;
  }finally{
   if(ticket===requestId){loading=false;refresh.disabled=false;refreshButtons();}
  }
 }
 confirm.addEventListener("change",refreshButtons);
 refresh.addEventListener("click",()=>{void load(dateInput.value);});
 dateInput.addEventListener("change",()=>{void load(dateInput.value);});
 manual.addEventListener("click",()=>showWebView("rph"));
 window.rphTodayLoad=()=>{void load(dateInput.value);};
})();
