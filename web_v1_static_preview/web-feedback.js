/* Private, same-origin Komen & Cadangan Web UI. No third-party SDK or IDs. */
(()=>{"use strict";
 const form=document.getElementById("web-feedback-form");
 const own=document.getElementById("web-feedback-own");
 const admin=document.getElementById("web-feedback-admin-list");
 const category=document.getElementById("web-feedback-category");
 const message=document.getElementById("web-feedback-message");
 const status=document.getElementById("web-feedback-status");
 const submit=document.getElementById("web-feedback-submit");
 if(!form||!own||!admin||!category||!message||!status||!submit)return;

 function info(node,text){node.textContent=text;}
 function element(tag,cls,value){
   const node=document.createElement(tag);
   if(cls)node.className=cls;
   node.textContent=String(value==null?"":value);
   return node;
 }
 function showRows(target, rows, forAdmin){
   target.replaceChildren();
   if(!Array.isArray(rows)||!rows.length){
     target.append(element("p","notice","Belum ada komen."));
     return;
   }
   for(const item of rows){
     const card=element("article","web-feedback-card","");
     const head=element("div","web-feedback-card-top","");
     head.append(element("strong","",item.category));
     const date=typeof item.created_at==="string"?
       new Date(item.created_at).toLocaleDateString("ms-MY",
         {day:"numeric",month:"short",year:"numeric"}):"";
     head.append(element("small","",date+" · "+(
       {baru:"Baharu",dibaca:"Dibaca",selesai:"Selesai"}[item.status]||"Dalam semakan")));
     card.append(head);
     if(forAdmin)card.append(element("small","web-feedback-owner",
       "ID Telegram: "+item.chat_id+" · Komen #"+item.id));
     card.append(element("p","web-feedback-text",item.feedback_text));
     target.append(card);
   }
 }
 async function response(url,options){
   const result=await fetch(url,{credentials:"same-origin",cache:"no-store",...options});
   const body=await result.json().catch(()=>({}));
   if(!result.ok)throw Error(body.error||"Sambungan komen belum tersedia");
   return body;
 }
 async function loadOwn(){
   info(own,"Memuatkan komen anda…");
   try{
     const data=await response("/api/web/feedback");
     showRows(own,data.items,false);
   }catch(e){info(own,e.message);}
 }
 async function loadAdmin(){
   info(admin,"Memuatkan komen terkini…");
   try{
     const data=await response("/api/web/admin/feedback");
     showRows(admin,data.items,true);
     if(data.limited)admin.prepend(element("p","notice",
       "Memaparkan 50 komen terkini. Komen lama masih tersimpan di Supabase."));
   }catch(e){info(admin,e.message);}
 }
 form.addEventListener("submit",async e=>{
   e.preventDefault();
   const value=message.value.trim();
   if(value.length<10||value.length>1500){
     info(status,"Tulis komen antara 10 hingga 1,500 aksara.");return;
   }
   submit.disabled=true;info(status,"Menyimpan komen…");
   try{
     const data=await response("/api/web/feedback",{
       method:"POST",headers:{"Content-Type":"application/json"},
       body:JSON.stringify({category:category.value,message:value})
     });
     message.value="";info(status,data.message||"Komen berjaya dihantar.");
     await loadOwn();
   }catch(err){info(status,err.message);}
   finally{submit.disabled=false;}
 });
 document.getElementById("web-feedback-refresh")?.addEventListener("click",loadOwn);
 document.getElementById("web-feedback-admin-refresh")?.addEventListener("click",loadAdmin);
 window.cikgulajuFeedbackLoad=loadOwn;
 window.cikgulajuFeedbackAdminLoad=loadAdmin;
})();