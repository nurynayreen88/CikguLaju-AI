"use strict";
(async function () {
  const box = document.getElementById("web-referral-details");
  const status = document.getElementById("web-referral-status");
  const linkInput = document.getElementById("web-referral-link");
  const copy = document.getElementById("web-referral-copy");
  const share = document.getElementById("web-referral-share");
  const tab = document.getElementById("web-referral-tab");
  const view = document.getElementById("view-referral");
  if (!box || !status || !linkInput || !copy || !share || !tab || !view) return;
  tab.hidden = true;
  view.hidden = true;
  function revoke() {
    tab.hidden = true;
    box.hidden = true;
    linkInput.value = "";
    if (!view.hidden) document.querySelector('[data-web-view="today"]')?.click();
    view.hidden = true;
  }
  async function update() {
    try {
      const r = await fetch("/api/web/referral", {credentials:"same-origin", cache:"no-store"});
      if (r.status === 401 || r.status === 403) { revoke(); return; }
      if (!r.ok) throw Error("Maklumat referral belum dapat dibaca.");
      const data = await r.json();
      if (data.enabled !== true) { revoke(); return; }
      if (typeof data.link !== "string" || !data.link.startsWith("https://cikgulaju-web.onrender.com/?ref=")) { revoke(); return; }
      tab.hidden = false;
      linkInput.value=data.link;
      document.getElementById("web-referral-signups").textContent=String(data.registered);
      document.getElementById("web-referral-paid").textContent=String(data.paid);
      document.getElementById("web-referral-points").textContent=String(data.points);
      box.hidden=false;
      status.textContent="Kongsi pautan ini. Mata hanya dikreditkan selepas pembayaran pertama disahkan.";
    } catch (_) {revoke(); status.textContent="Maklumat referral belum tersedia. Cuba muat semula halaman.";}
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
  tab.addEventListener("click",update);
  window.cikgulajuReferralInit = () => update();
})();
