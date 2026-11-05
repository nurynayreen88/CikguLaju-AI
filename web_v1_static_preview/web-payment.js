"use strict";
/* Web payment uses authenticated server-side QR, current Telegram prices,
 * the same Supabase pending queue, and admin approval. Never mark paid here. */
const payView=document.getElementById("view-payment");
const payStatus=document.getElementById("web-payment-status");
const payMessage=document.getElementById("payment-message");
const payEntry=document.getElementById("payment-entry");
const payPlan=document.getElementById("payment-plan");
const payDesc=document.getElementById("payment-plan-description");
const payReceipt=document.getElementById("payment-receipt");
const paySubmit=document.getElementById("payment-submit");
const payQr=document.getElementById("payment-qr-image");
const payQrNotice=document.getElementById("payment-qr-notice");
const payRefresh=document.getElementById("payment-refresh");
let payCatalog=null;
let payQrUrl=null;
let payBusy=false;

function paymentReady(){
  const file=payReceipt.files?.[0], choice=payCatalog?.plans?.find(p=>p.code===payPlan.value);
  paySubmit.disabled=payBusy||!choice||!file||file.size>4*1024*1024||file.size<700
    ||!["image/jpeg","image/png","image/webp","application/pdf"].includes(file.type);
}
function clearPaymentQr(){
  if(payQrUrl)URL.revokeObjectURL(payQrUrl);
  payQrUrl=null;
  payQr.hidden=true;
  payQr.removeAttribute("src");
}
async function paymentApi(path,options={}){
  const r=await fetch(path,{credentials:"same-origin",cache:"no-store",...options});
  const mime=(r.headers.get("Content-Type")||"").split(";")[0].toLowerCase();
  const body=mime==="application/json"?await r.json().catch(()=>({})):{};
  if(!r.ok)throw Error(body.error||"Sambungan bayaran gagal (HTTP "+r.status+").");
  return body;
}
async function loadWebPayments(){
  payBusy=true;paymentReady();
  payStatus.textContent="Menyemak permohonan bayaran…";
  payMessage.textContent="";
  try{
    const data=await paymentApi("/api/web/payment/catalog");
    if(!Array.isArray(data.plans)||!data.plans.length)throw Error("Pakej belum tersedia");
    payCatalog=data;
    payPlan.replaceChildren(new Option("Pilih pakej bayaran",""));
    for(const p of data.plans){
      if(typeof p.code!=="string"||typeof p.amount!=="string")continue;
      payPlan.add(new Option(p.label+" • RM"+p.amount,p.code));
    }
    payPlan.disabled=false;
    const pending=data.status?.pending===true;
    payEntry.hidden=pending;
    if(pending){
      const status=data.status;
      payStatus.textContent="⌛ RESIT MENUNGGU PENGESAHAN ADMIN\n"
        +"Permohonan #"+status.id+" • RM"+status.amount
        +"\nResit diterima. Jangan bayar sekali lagi.";
      clearPaymentQr();
    }else{
      payStatus.textContent="Tiada permohonan Pending. Pilih pakej, buat bayaran dan hantar resit sebenar.";
    }
    payReceipt.value="";
    payPlan.value="";
    payDesc.textContent="";
    clearPaymentQr();
    payQrNotice.textContent="Pilih pakej untuk melihat QR DuitNow.";
  }catch(error){
    payCatalog=null;
    payEntry.hidden=true;
    clearPaymentQr();
    payStatus.textContent="Status pembayaran belum dapat disemak dengan selamat.";
    payMessage.textContent=error.message+" Jangan buat bayaran baharu sehingga status boleh disahkan.";
  }finally{payBusy=false;paymentReady();}
}

async function loadPaymentQr(){
  clearPaymentQr();
  payQrNotice.textContent="Memuatkan QR rasmi…";
  try{
    const r=await fetch("/api/web/payment/qr",{credentials:"same-origin",cache:"no-store"});
    if(!r.ok){
      const data=await r.json().catch(()=>({}));
      throw Error(data.error||"QR DuitNow belum tersedia.");
    }
    const mime=(r.headers.get("Content-Type")||"").split(";")[0].toLowerCase();
    if(!["image/png","image/jpeg"].includes(mime))throw Error("QR tidak sah.");
    const image=await r.blob();
    if(image.size<800||image.size>2*1024*1024)throw Error("Saiz QR tidak sah.");
    payQrUrl=URL.createObjectURL(image);
    payQr.src=payQrUrl;
    payQr.hidden=false;
    payQrNotice.textContent="Imbas menggunakan aplikasi perbankan dan bayar jumlah tepat pakej.";
  }catch(error){payQrNotice.textContent=error.message;}
}
payPlan.addEventListener("change",()=>{
  const p=payCatalog?.plans?.find(row=>row.code===payPlan.value);
  payDesc.textContent=p?(p.description+" • RM"+p.amount+" (DuitNow)"):"";
  paymentReady();
  if(p)void loadPaymentQr();
  else {clearPaymentQr();payQrNotice.textContent="Pilih pakej untuk melihat QR DuitNow.";}
});
payReceipt.addEventListener("change",()=>{
  const f=payReceipt.files?.[0];
  if(f&&(f.size>4*1024*1024||f.size<700))payMessage.textContent="Resit mesti berukuran antara 700 B hingga 4 MB.";
  else payMessage.textContent="";
  paymentReady();
});
paySubmit.addEventListener("click",async()=>{
  const p=payCatalog?.plans?.find(row=>row.code===payPlan.value),f=payReceipt.files?.[0];
  if(!p||!f||payBusy)return;
  if(!window.confirm("Sahkan anda telah membuat bayaran RM"+p.amount+
      " bagi "+p.label+" dan mahu menghantar resit untuk pengesahan admin?"))return;
  payBusy=true;paymentReady();payMessage.textContent="Menghantar resit dan menyemak rekod Pending…";
  try{
    const body=new FormData();body.append("plan",p.code);body.append("receipt",f,f.name);
    const result=await paymentApi("/api/web/payment/receipt",{method:"POST",body});
    if(!result.submitted||!result.id)throw Error("Rekod bayaran tidak dapat disahkan.");
    await loadWebPayments();
    payMessage.textContent="Resit permohonan #"+result.id+" diterima. Menunggu pengesahan admin.";
  }catch(error){
    payMessage.textContent=error.message;
    // Confirm server state; avoid accidentally duplicating an already-saved proof.
    try{await loadWebPayments();}catch(_ignored){}
    payMessage.textContent=error.message;
  }finally{payBusy=false;paymentReady();}
});
payRefresh.addEventListener("click",()=>void loadWebPayments());
document.querySelector('[data-web-view="payment"]').addEventListener("click",()=>void loadWebPayments());
window.addEventListener("pagehide",clearPaymentQr);
