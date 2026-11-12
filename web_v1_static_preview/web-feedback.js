/* Private, same-origin Komen & Cadangan Web UI. No third-party SDK or IDs. */
(()=>{"use strict";
 const form=document.getElementById("web-feedback-form");
 const own=document.getElementById("web-feedback-own");
 const admin=document.getElementById("web-feedback-admin-list");
 const category=document.getElementById("web-feedback-category");
 const message=document.getElementById("web-feedback-message");
 const status=document.getElementById("web-feedback-status");
 const submit=document.getElementById("web-feedback-submit");
 const adminFilter=document.getElementById("web-feedback-admin-filter");
 const adminMore=document.getElementById("web-feedback-admin-more");
 let adminNextBefore=null;
 let adminLoading=false;
 if(!form||!own||!admin||!category||!message||!status||!submit)return;

 function info(node,text){node.textContent=text;}
 function element(tag,cls,value){
   const node=document.createElement(tag);
   if(cls)node.className=cls;
   node.textContent=String(value==null?"":value);
   return node;
 }
 function showRows(target, rows, forAdmin, append=false){
   if(!append)target.replaceChildren();
   if(!Array.isArray(rows)||!rows.length){
     if(!append)target.append(element("p","notice","Belum ada komen."));
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
     if(forAdmin){
       const actions=element("div","web-feedback-admin-actions","");
       const label=element("label","", "Tukar status: ");
       const chooser=document.createElement("select");
       chooser.setAttribute("aria-label","Status komen #"+item.id);
       for(const [value,title] of [["baru","Baharu"],["dibaca","Dibaca"],["selesai","Selesai"]]){
         const option=document.createElement("option");
         option.value=value;option.textContent=title;chooser.append(option);
       }
       chooser.value=item.status;
       label.append(chooser);
       const save=element("button","profile-refresh","Simpan Status");
       save.type="button";
       const note=element("span","notice","");
       note.setAttribute("role","status");
       save.addEventListener("click",async()=>{
         if(chooser.value===item.status){note.textContent="Status masih sama.";return;}
         save.disabled=true;
         note.textContent="Menyimpan status…";
         try{
           await response("/api/web/admin/feedback/"+encodeURIComponent(String(item.id)),{
             method:"PATCH",headers:{"Content-Type":"application/json"},
             body:JSON.stringify({status:chooser.value})
           });
           note.textContent="Status dikemas kini.";
           await loadAdmin();
         }catch(err){note.textContent=err.message||"Status tidak dapat disimpan.";}
         finally{save.disabled=false;}
       });
       actions.append(label,save,note);
       card.append(actions);
     }
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
 async function loadAdmin(append=false){
   if(adminLoading)return;
   if(append&&!adminNextBefore)return;
   adminLoading=true;
   if(!append){
     adminNextBefore=null;
     info(admin,"Memuatkan komen terkini…");
   }
   if(adminMore)adminMore.disabled=true;
   try{
     const params=new URLSearchParams();
     if(adminFilter?.value&&adminFilter.value!=="semua"){
       params.set("status",adminFilter.value);
     }
     if(append)params.set("before",String(adminNextBefore));
     const query=params.toString();
     const data=await response("/api/web/admin/feedback"+(query?"?"+query:""));
     if(!Array.isArray(data.items)||typeof data.has_more!=="boolean"||
        (data.has_more&&(!Number.isSafeInteger(data.next_before)||data.next_before<=0))){
       throw Error("Format senarai komen tidak lengkap.");
     }
     showRows(admin,data.items,true,append);
     adminNextBefore=data.has_more?data.next_before:null;
     if(adminMore)adminMore.hidden=!data.has_more;
   }catch(e){
     if(!append)info(admin,e.message);
     else admin.append(element("p","notice",e.message||"Gagal memuatkan komen terdahulu."));
   }finally{
     adminLoading=false;
     if(adminMore)adminMore.disabled=false;
   }
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
 document.getElementById("web-feedback-admin-refresh")?.addEventListener("click",()=>void loadAdmin());
 adminFilter?.addEventListener("change",()=>void loadAdmin());
 adminMore?.addEventListener("click",()=>void loadAdmin(true));
 window.cikgulajuFeedbackLoad=loadOwn;
 window.cikgulajuFeedbackAdminLoad=()=>loadAdmin();
})();