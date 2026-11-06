"use strict";
(async function () {
  const box = document.getElementById("web-referral-details");
  const status = document.getElementById("web-referral-status");
  const linkInput = document.getElementById("web-referral-link");
  const copy = document.getElementById("web-referral-copy");
  const share = document.getElementById("web-referral-share");
  if (!box || !status || !linkInput || !copy || !share) return;
  async function update() {
    try {
      const r = await fetch("/api/web/referral", {credentials:"same-origin", cache:"no-store"});
      if (r.status === 401) return;
      if (!r.ok) throw Error("Maklumat referral belum dapat dibaca.");
      const data = await r.json();
      if (!data.enabled) {status.textContent="Program referral tertutup. Akaun ini belum diaktifkan oleh admin."; return;}
      linkInput.value=data.link;
      document.getElementById("web-referral-signups").textContent=String(data.registered);
      document.getElementById("web-referral-paid").textContent=String(data.paid);
      document.getElementById("web-referral-points").textContent=String(data.points);
      box.hidden=false;
      status.textContent="Kongsi pautan ini. Mata hanya dikreditkan selepas pembayaran pertama disahkan.";
    } catch (_) {status.textContent="Maklumat referral belum tersedia. Cuba muat semula halaman.";}
  }
  copy.addEventListener("click", async () => {
    try {await navigator.clipboard.writeText(linkInput.value);status.textContent="Pautan Web referral disalin.";}
    catch (_) {linkInput.focus();linkInput.select();status.textContent="Pilih dan salin pautan referral di atas.";}
  });
  share.addEventListener("click", async () => {
    if (navigator.share) {
      try {await navigator.share({title:"CikguLaju AI",text:"Cuba CikguLaju AI di Web",url:linkInput.value});}
      catch (_) { /* Cancelled share is not a failure. */ }
    } else {
      const url="https://wa.me/?text="+encodeURIComponent("Cuba CikguLaju AI di Web: "+linkInput.value);
      window.open(url,"_blank","noopener,noreferrer");
    }
  });
  void update();
  document.querySelectorAll('[data-web-view="referral"]').forEach(button => button.addEventListener("click",update));
})();
