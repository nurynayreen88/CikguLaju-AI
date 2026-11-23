/* CikguLaju private two-way support chat; identity always server-authenticated. */
(()=>{"use strict";
const $=id=>document.getElementById(id);
const own=$("web-chat-messages"), admin=$("web-admin-chat-thread");
if(!own||!admin)return;
let activeUser="";
function render(node,items,forAdmin=false){
  node.replaceChildren();
  if(!items.length){node.textContent="Belum ada mesej.";return;}
  for(const item of items){
    const bubble=document.createElement("div");
    bubble.className="web-chat-bubble "+(item.sender_role==="admin"?"admin":"");
    const head=document.createElement("small");
    const when=new Date(item.created_at).toLocaleString("ms-MY");
    head.textContent=(item.sender_role==="admin"?"Admin":"Pengguna")+" · "+when;
    const body=document.createElement("div");
    body.textContent=item.message;
    bubble.append(head,body);
    if(item.attachment_name){
      const link=document.createElement("a");
      link.href=(forAdmin?"/api/web/admin/chat-attachments/":"/api/web/chat/attachments/")+item.id;
      link.textContent="📎 Muat Turun: "+item.attachment_name;
      link.rel="noopener";link.download="";
      bubble.append(link);
    }
    node.append(bubble);
  }
  node.scrollTop=node.scrollHeight;
}
async function api(path,opts){
  const r=await fetch(path,{credentials:"same-origin",cache:"no-store",...opts});
  const j=await r.json().catch(()=>({}));
  if(!r.ok)throw Error(j.error||"Sambungan chat gagal");
  return j;
}
async function ownLoad(){
  try{render(own,(await api("/api/web/chat")).items);$("web-chat-status").textContent="";}
  catch(e){$("web-chat-status").textContent=e.message;}
}
$("web-chat-refresh").addEventListener("click",ownLoad);
$("web-chat-form").addEventListener("submit",async e=>{
  e.preventDefault();
  const box=$("web-chat-input"),message=box.value.trim();
  const file=$("web-chat-file").files[0];
  if(!message&&!file)return;
  if(file&&file.size>4*1024*1024){$("web-chat-status").textContent="Lampiran melebihi 4 MB.";return;}
  try{
    const options=file?{method:"POST",body:(()=>{
      const data=new FormData();data.append("message",message);data.append("file",file);return data;
    })()}:{method:"POST",headers:{"Content-Type":"application/json"},
      body:JSON.stringify({message})};
    await api("/api/web/chat",options);
    box.value="";$("web-chat-file").value="";await ownLoad();$("web-chat-status").textContent="Mesej dihantar.";
  }catch(err){$("web-chat-status").textContent=err.message;}
});
async function adminLoad(){
  try{
    const data=await api("/api/web/admin/chats");
    const box=$("web-admin-chat-inbox");box.replaceChildren();
    for(const row of data.items){
      const b=document.createElement("button");b.type="button";
      b.textContent="ID "+row.user_id+" · "+row.last_message;
      b.addEventListener("click",()=>openThread(row.user_id));box.append(b);
    }
    if(!data.items.length)box.textContent="Belum ada chat pengguna.";
  }catch(e){$("web-admin-chat-status").textContent=e.message;}
}
async function openThread(id){
  if(!/^[1-9][0-9]{0,18}$/.test(id)||BigInt(id)>9223372036854775807n){
    $("web-admin-chat-status").textContent="ID pengguna tidak sah.";return;
  }
  activeUser=id;$("web-admin-chat-user").value=id;
  try{render(admin,(await api("/api/web/admin/chats/"+id)).items,true);
    $("web-admin-chat-status").textContent="Perbualan ID "+id;
  }catch(e){$("web-admin-chat-status").textContent=e.message;}
}
$("web-admin-chat-open").addEventListener("click",()=>openThread($("web-admin-chat-user").value.trim()));
$("web-admin-chat-refresh").addEventListener("click",adminLoad);
$("web-admin-chat-form").addEventListener("submit",async e=>{
  e.preventDefault();
  if(!activeUser){$("web-admin-chat-status").textContent="Pilih ID pengguna dahulu.";return;}
  const box=$("web-admin-chat-input"),message=box.value.trim();
  const file=$("web-admin-chat-file").files[0];if(!message&&!file)return;
  if(file&&file.size>4*1024*1024){$("web-admin-chat-status").textContent="Lampiran melebihi 4 MB.";return;}
  try{
    const options=file?{method:"POST",body:(()=>{
      const data=new FormData();data.append("message",message);data.append("file",file);return data;
    })()}:{method:"POST",headers:{"Content-Type":"application/json"},body:JSON.stringify({message})};
    await api("/api/web/admin/chats/"+activeUser,options);
    box.value="";$("web-admin-chat-file").value="";await openThread(activeUser);
  }catch(err){$("web-admin-chat-status").textContent=err.message;}
});
document.querySelectorAll('[data-web-view="feedback"]').forEach(b=>
  b.addEventListener("click",ownLoad));
document.querySelectorAll('[data-web-view="admin"]').forEach(b=>
  b.addEventListener("click",adminLoad));
})();
