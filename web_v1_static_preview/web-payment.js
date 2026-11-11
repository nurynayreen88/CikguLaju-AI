"use strict";
/* One current offer: RM20 Rakan Pembangun. The participation percentage is
 * read from Telegram's approved entitlement RPC, never a hardcoded estimate.
 * Receipt and membership confirmation remain server-side and admin reviewed. */
const payStatus=document.getElementById("web-payment-status");
const payMessage=document.getElementById("payment-message");
const payEntry=document.getElementById("payment-entry");
const payPlan=document.getElementById("payment-plan");
const payDesc=document.getElementById("payment-plan-description");
const payReceipt=document.getElementById("payment-receipt");
const paySubmit=document.getElementById("payment-submit");
const payQr=document.getElementById("payment-qr-image");
const payQrNotice=document.getElementById("payment-qr-notice");
const payDirectLink=document.getElementById("payment-direct-link");
const payRefresh=document.getElementById("payment-refresh");
const payProgress=document.getElementById("rakan-progress");
const payPercent=document.getElementById("rakan-progress-percent");
const payProgressFill=document.getElementById("rakan-progress-fill");
const payProgressBar=document.getElementById("rakan-progress-bar");
let payCatalog=null;
let payQrUrl=null;
let payBusy=false;

function paymentReady(){
  const file=payReceipt.files?.[0];
  const choice=payCatalog?.plans?.find(p=>p.code==="rakan_pembangun"&&p.amount==="20.00");
  paySubmit.disabled=payBusy||payEntry.hidden||!choice||!file
    ||file.size>4*1024*1024||file.size<700
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
function setVerifiedProgress(data){
  const percent=data.progress_percentage;
  if(typeof percent!=="string"||!/^(?:[0-9]{1,2}\.[0-9]|100\.0)%$/.test(percent)
      ||typeof data.rakan_open!=="boolean"
      ||typeof data.already_member!=="boolean")throw Error("Status keahlian tidak disahkan.");
  const value=Number(percent.slice(0,-1));
  if(!Number.isFinite(value)||value<0||value>100)throw Error("Peratus penyertaan tidak sah.");
  payPercent.textContent=percent;
  payProgressFill.style.width=value+"%";
  payProgressBar.setAttribute("aria-valuenow",String(value));
  payProgress.hidden=false;
}
async function loadWebPayments(){
  payBusy=true;
  payEntry.hidden=true;
  payDirectLink.hidden=true;
  payProgress.hidden=true;
  clearPaymentQr();
  paymentReady();
  payStatus.textContent="Menyemak status Rakan Pembangun…";
  payMessage.textContent="";
  try{
    const data=await paymentApi("/api/web/payment/catalog");
    if(!Array.isArray(data.plans)||data.plans.length!==1
       ||data.plans[0].code!=="rakan_pembangun"
       ||data.plans[0].amount!=="20.00")throw Error("Pakej Rakan Pembangun belum dapat disahkan.");
    setVerifiedProgress(data);
    payCatalog=data;
    payPlan.value="rakan_pembangun";
    payDesc.textContent=data.plans[0].description+" • RM20.00 (sekali bayar)";
    const pending=data.status?.pending===true;
    const active=data.already_member===true;
    const available=data.rakan_open===true;
    const canPay=!pending&&!active&&available;
    payEntry.hidden=!canPay;
    payDirectLink.hidden=!canPay;
    payReceipt.value="";
    if(pending){
      const status=data.status;
      payStatus.textContent="⌛ RESIT MENUNGGU PENGESAHAN ADMIN\n"
        +"Permohonan #"+status.id+" • RM"+status.amount
        +"\nJangan buat bayaran sekali lagi.";
    }else if(active){
      payStatus.textContent="✅ Rakan Pembangun anda sudah AKTIF. Tidak perlu membuat bayaran lagi.";
    }else if(!available){
      payStatus.textContent="Pendaftaran Rakan Pembangun Early Bird telah penuh. Bayaran baharu tidak diterima.";
    }else{
      payStatus.textContent="Rakan Pembangun RM20 sekali bayar tersedia. Bayar menggunakan QR atau link, kemudian hantar resit.";
    }
    payQrNotice.textContent="Memuatkan QR DuitNow rasmi…";
    if(canPay)void loadPaymentQr();
  }catch(error){
    payCatalog=null;
    payEntry.hidden=true;
    payDirectLink.hidden=true;
    payProgress.hidden=true;
    clearPaymentQr();
    payStatus.textContent="Status Rakan Pembangun belum dapat disemak dengan selamat.";
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
    if(payEntry.hidden)return; // New status may have disabled the offer.
    payQrUrl=URL.createObjectURL(image);
    payQr.src=payQrUrl;
    payQr.hidden=false;
    payQrNotice.textContent="Bayar RM20.00 menggunakan aplikasi perbankan, kemudian hantar resit.";
  }catch(error){if(!payEntry.hidden)payQrNotice.textContent=error.message;}
}
payReceipt.addEventListener("change",()=>{
  const f=payReceipt.files?.[0];
  if(f&&(f.size>4*1024*1024||f.size<700))payMessage.textContent="Resit mesti berukuran antara 700 B hingga 4 MB.";
  else payMessage.textContent="";
  paymentReady();
});
paySubmit.addEventListener("click",async()=>{
  const p=payCatalog?.plans?.find(row=>row.code==="rakan_pembangun"&&row.amount==="20.00");
  const f=payReceipt.files?.[0];
  if(!p||!f||payBusy||payEntry.hidden)return;
  if(!window.confirm("Sahkan anda telah membayar RM20 sekali untuk Rakan Pembangun dan ingin menghantar resit bagi semakan admin?"))return;
  payBusy=true;paymentReady();
  payMessage.textContent="Menghantar resit dan menyemak rekod Pending…";
  try{
    const body=new FormData();
    body.append("plan","rakan_pembangun");
    body.append("receipt",f,f.name);
    const result=await paymentApi("/api/web/payment/receipt",{method:"POST",body});
    if(!result.submitted||!result.id)throw Error("Rekod bayaran tidak dapat disahkan.");
    await loadWebPayments();
    payMessage.textContent="Resit permohonan #"+result.id+" diterima. Menunggu pengesahan admin.";
  }catch(error){
    // Read current state first to avoid duplicate payments after a response loss.
    await loadWebPayments();
    payMessage.textContent=error.message;
  }finally{payBusy=false;paymentReady();}
});
payRefresh.addEventListener("click",()=>void loadWebPayments());
document.querySelector('[data-web-view="payment"]').addEventListener("click",()=>void loadWebPayments());
window.addEventListener("pagehide",clearPaymentQr);
