/* CikguLaju private two-way support chat; identity always server-authenticated. */
(()=>{"use strict";
const $=id=>document.getElementById(id);
const own=$("web-chat-messages"), admin=$("web-admin-chat-thread");
if(!own||!admin)return;
let activeUser="";
const topChat=$("web-chat-top"),badge=$("web-chat-unread-badge"),
  unreadLabel=$("web-chat-unread-label"),toast=$("web-chat-alert"),
  toastText=$("web-chat-alert-text"),hint=$("web-chat-top-hint"),
  workspace=$("workspace");
const originalTitle=document.title;
let unreadChecking=false,ownLoading=false;
function updateNotice(count){
  const unread=Number.isInteger(count)&&count>0?count:0;
  badge.hidden=unread===0;
  unreadLabel.hidden=unread===0;
  badge.textContent=unread>=99?"99+":String(unread);
  topChat.classList.toggle("has-unread",unread>0);
  hint.textContent=unread>0?"Tekan untuk baca":"Buka perbualan";
  toast.hidden=unread===0;
  toastText.textContent=unread>=99?"99+ mesej baharu daripada admin":
    unread+" mesej baharu daripada admin";
  document.title=unread>0?"("+ (unread>=99?"99+":unread) +") "+originalTitle:originalTitle;
}
async function checkUnread(){
  if(unreadChecking||!workspace||workspace.hidden||document.hidden)return;
  unreadChecking=true;
  try{
    const data=await api("/api/web/chat/unread");
    if(!Number.isInteger(data.unread_count)||data.unread_count<0)
      throw Error("Status notifikasi tidak sah");
    updateNotice(data.unread_count);
    if(topChat.open&&data.unread_count>0&&!ownLoading)void ownLoad();
  }catch(_error){/* Keep the last verified unread count visible. */}
  finally{unreadChecking=false;}
}
function openOwnChat(){
  topChat.open=true;
  topChat.scrollIntoView({block:"start",behavior:"smooth"});
  void ownLoad();
}
topChat.addEventListener("toggle",()=>{if(topChat.open)void ownLoad();});
toast.addEventListener("click",openOwnChat);
document.addEventListener("visibilitychange",()=>{if(!document.hidden)void checkUnread();});
window.addEventListener("focus",()=>void checkUnread());
window.cikgulajuChatOnLogin=()=>void checkUnread();
if(workspace){
  new MutationObserver(()=>{if(!workspace.hidden)void checkUnread();})
    .observe(workspace,{attributes:true,attributeFilter:["hidden"]});
}
setInterval(()=>void checkUnread(),60000);
if(!workspace?.hidden)void checkUnread();
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
  if(ownLoading||!topChat.open)return;
  ownLoading=true;
  try{
    const data=await api("/api/web/chat");
    const items=Array.isArray(data.items)?data.items:[];
    render(own,items);
    $("web-chat-status").textContent="";
    const latestAdmin=[...items].reverse().find(item=>item.sender_role==="admin");
    if(latestAdmin && Number.isSafeInteger(latestAdmin.id) && latestAdmin.id>0){
      await api("/api/web/chat/read",{
        method:"POST",headers:{"Content-Type":"application/json"},
        body:JSON.stringify({last_seen_admin_id:String(latestAdmin.id)})
      });
    }
    void checkUnread();
  }catch(e){$("web-chat-status").textContent=e.message;}
  finally{ownLoading=false;}
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
  try{
    const data=await api("/api/web/admin/chats/"+id);
    const items=Array.isArray(data.items)?data.items:[];
    render(admin,items,true);
    $("web-admin-chat-status").textContent="Perbualan ID "+id;
    const latestUser=[...items].reverse().find(item=>item.sender_role==="user");
    // Only mark messages as read after the selected conversation was rendered.
    if(latestUser&&Number.isSafeInteger(latestUser.id)&&latestUser.id>0){
      try{
        await api("/api/web/admin/chats/"+id+"/read",{
          method:"POST",headers:{"Content-Type":"application/json"},
          body:JSON.stringify({last_seen_user_id:String(latestUser.id)})
        });
        window.cikgulajuAdminNotificationsRefresh?.();
      }catch(_error){
        $("web-admin-chat-status").textContent="Perbualan dibuka, tetapi status dibaca belum disimpan.";
      }
    }
  }catch(e){$("web-admin-chat-status").textContent=e.message;}
}
$("web-admin-chat-open").addEventListener("click",()=>openThread($("web-admin-chat-user").value.trim()));
// The directory uses this public UI function; the server still authorizes every request.
window.cikgulajuOpenAdminChat=async id=>{
  const tab=$("web-admin-tab");
  if(!tab||tab.hidden)throw Error("Akses chat admin belum tersedia.");
  const top=$("web-admin-top"),view=$("view-admin");
  if(top)top.open=true;
  if(view)view.hidden=false;
  tab.click();
  await openThread(String(id));
  $("web-chat-admin-heading")?.scrollIntoView({block:"start",behavior:"auto"});
  $("web-admin-chat-input")?.focus({preventScroll:true});
};
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
    window.cikgulajuAdminNotificationsRefresh?.();
  }catch(err){$("web-admin-chat-status").textContent=err.message;}
});
// Chat lives at the top; the feedback tab is reserved for comments.
document.querySelectorAll('[data-web-view="admin"]').forEach(b=>
  b.addEventListener("click",adminLoad));
})();
