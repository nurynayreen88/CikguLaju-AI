"use strict";
(async function () {
  const get = id => document.getElementById(id);
  const box = get("web-referral-details");
  const status = get("web-referral-status");
  const linkInput = get("web-referral-link");
  const copy = get("web-referral-copy");
  const share = get("web-referral-share");
  const tab = get("web-referral-tab");
  const view = get("view-referral");
  const claimPanel = get("web-affiliate-claim");
  const walletForm = get("affiliate-wallet-form");
  const claimForm = get("affiliate-claim-form");
  const phone = get("affiliate-phone");
  const confirm = get("affiliate-confirm");
  const amount = get("affiliate-amount");
  const claimStatus = get("affiliate-status");
  const history = get("affiliate-history");
  const admin = get("affiliate-admin");
  const filter = get("affiliate-admin-filter");
  const adminStatus = get("affiliate-admin-status");
  const adminList = get("affiliate-admin-list");
  const more = get("affiliate-admin-more");
  if (!box || !status || !linkInput || !copy || !share || !tab || !view || !claimPanel || !admin) return;

  const labels = {pending:"Menunggu", processing:"Dalam Proses", paid:"Dibayar", rejected:"Ditolak"};
  const money = value => Number(value).toLocaleString("en-MY", {minimumFractionDigits:2, maximumFractionDigits:2});
  const date = value => new Date(value).toLocaleString("ms-MY", {timeZone:"Asia/Kuala_Lumpur"});
  const deepLink = new URLSearchParams(window.location.search).get("affiliate") === "1";
  let openFromTelegram = deepLink;
  let savedPhone = "";
  let available = 0;
  let requestKey;
  let requestIdentity;
  let page = 0;
  let submitting = false;
  tab.hidden = true;
  view.hidden = true;

  async function api(path, options) {
    const r = await fetch(path, {credentials:"same-origin", cache:"no-store", ...options});
    const data = await r.json().catch(() => ({}));
    if (!r.ok) throw new Error(data.error || "Rekod affiliate belum dapat dibaca.");
    return data;
  }
  function jsonPost(body) {
    return {method:"POST", headers:{"Content-Type":"application/json"}, body:JSON.stringify(body)};
  }
  function revoke() {
    tab.hidden = true;
    box.hidden = true;
    claimPanel.hidden = true;
    linkInput.value = "";
    phone.value = savedPhone = "";
    history.replaceChildren();
    confirm.checked = false;
    if (!view.hidden) document.querySelector('[data-web-view="today"]')?.click();
    view.hidden = true;
  }
  function syncSubmit() {
    get("affiliate-submit").disabled = submitting || !savedPhone || phone.value !== savedPhone || !confirm.checked || available < 10;
  }
  function showClaims(data) {
    claimPanel.hidden = !data.open;
    if (!data.open) return;
    const nextPhone = data.phone || "";
    if (phone.value === savedPhone) phone.value = nextPhone;
    if (nextPhone !== savedPhone) confirm.checked = false;
    savedPhone = nextPhone;
    available = Number(data.available);
    get("affiliate-available").textContent = money(available);
    amount.max = String(available);
    claimForm.hidden = !savedPhone || available < 10;
    get("affiliate-save-wallet").textContent = savedPhone ? "Simpan Nombor" : "Sertai Affiliate";
    history.replaceChildren();
    for (const row of data.claims) {
      const li = document.createElement("li");
      li.textContent = `${date(row.requested_at)} · RM${money(row.points)} · ${labels[row.status]}`
        + (row.payment_reference ? ` · Rujukan ${row.payment_reference}` : "")
        + (row.rejection_reason ? ` · ${row.rejection_reason}` : "");
      history.append(li);
    }
    if (!data.claims.length) {
      const li = document.createElement("li");
      li.textContent = "Belum ada tuntutan.";
      history.append(li);
    }
    syncSubmit();
  }
  async function update() {
    try {
      const data = await api("/api/web/referral");
      if (data.enabled !== true) {
        if (data.can_join !== true) { revoke(); return; }
        box.hidden = true;
        linkInput.value = "";
        status.textContent = "Simpan nombor telefon TNG eWallet untuk menyertai affiliate dan mendapat pautan jemputan.";
      } else {
        if (typeof data.link !== "string" || !data.link.startsWith("https://cikgulaju-web.onrender.com/?ref=")) { revoke(); return; }
        linkInput.value = data.link;
        get("web-referral-signups").textContent = String(data.registered);
        get("web-referral-paid").textContent = String(data.paid);
        get("web-referral-points").textContent = String(data.points);
        box.hidden = false;
        status.textContent = "Mata dikreditkan selepas bayaran pertama disahkan.";
      }
      tab.hidden = false;
      try {
        const details = await api("/api/web/affiliate");
        showClaims(details);
        if (details.open && data.enabled) status.textContent = `Ganjaran ${details.rate}% bagi bayaran pertama yang disahkan.`;
      } catch (_) {
        claimPanel.hidden = true;
      }
      if (openFromTelegram) {
        openFromTelegram = false;
        tab.click();
      }
    } catch (_) { revoke(); }
  }

  phone.addEventListener("input", () => { confirm.checked = false; syncSubmit(); });
  confirm.addEventListener("change", syncSubmit);
  walletForm.addEventListener("submit", async event => {
    event.preventDefault();
    const button = get("affiliate-save-wallet");
    button.disabled = true;
    try {
      await api("/api/web/affiliate/wallet", jsonPost({phone:phone.value, confirmed:confirm.checked}));
      phone.value = savedPhone;
      await update();
      claimStatus.textContent = "Nombor TNG eWallet disimpan.";
    } catch (error) { claimStatus.textContent = error.message; }
    finally { button.disabled = false; }
  });
  claimForm.addEventListener("submit", async event => {
    event.preventDefault();
    if (get("affiliate-submit").disabled) return;
    const identity = `${savedPhone}/${amount.value}`;
    if (requestIdentity !== identity) {
      requestIdentity = identity;
      requestKey = crypto.randomUUID();
    }
    submitting = true;
    syncSubmit();
    try {
      await api("/api/web/affiliate/claims", jsonPost({phone:savedPhone, confirmed:confirm.checked, points:amount.value, key:requestKey}));
      requestIdentity = requestKey = undefined;
      amount.value = "";
      confirm.checked = false;
      await update();
      claimStatus.textContent = "Tuntutan diterima. Mata ini dikunci sementara admin memproses bayaran.";
    } catch (error) { claimStatus.textContent = error.message; }
    finally { submitting = false; syncSubmit(); }
  });

  copy.addEventListener("click", async () => {
    try {await navigator.clipboard.writeText(linkInput.value);status.textContent="Pautan affiliate disalin.";}
    catch (_) {linkInput.focus();linkInput.select();status.textContent="Pilih dan salin pautan affiliate di atas.";}
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

  function actionForm(claimId, action, label, fields) {
    const form = document.createElement("form");
    form.className = "teacher-profile-form";
    for (const [name, description, type] of fields) {
      const wrapper = document.createElement("label");
      wrapper.textContent = description;
      const input = document.createElement("input");
      input.name = name;
      input.type = type;
      input.required = true;
      if (type === "file") input.accept = "image/png,image/jpeg,application/pdf";
      else input.maxLength = name === "reason" ? 500 : 80;
      wrapper.append(input);
      form.append(wrapper);
    }
    const button = document.createElement("button");
    button.textContent = label;
    button.type = "submit";
    form.append(button);
    form.addEventListener("submit", async event => {
      event.preventDefault();
      button.disabled = true;
      const data = new FormData(form);
      data.set("action", action);
      try {
        await api(`/api/web/admin/affiliate/claims/${claimId}`, {method:"POST", body:data});
        if (action === "processing") filter.value = "processing";
        await updateAdmin();
        adminStatus.textContent = "Status tuntutan dikemas kini.";
      } catch (error) { adminStatus.textContent = error.message; }
      finally { button.disabled = false; }
    });
    return form;
  }
  async function updateAdmin(append = false) {
    if (!append) page = 0;
    const requestedStatus = filter.value;
    const requestedPage = page;
    try {
      const data = await api(`/api/web/admin/affiliate/claims?status=${requestedStatus}&page=${requestedPage}`);
      if (requestedStatus !== filter.value || requestedPage !== page) return;
      admin.hidden = !data.open;
      if (!append) adminList.replaceChildren();
      more.hidden = !data.more;
      adminStatus.textContent = data.items.length ? "" : "Tiada tuntutan bagi status ini.";
      for (const item of data.items) {
        const section = document.createElement("section");
        section.className = "teacher-timetable-section";
        const line = document.createElement("p");
        line.textContent = `Akaun ${item.user_id} · TNG ${item.phone_snapshot} · RM${money(item.points)} · ${date(item.requested_at)} · ${labels[item.status]}`
          + (item.payment_reference ? ` · Rujukan ${item.payment_reference}` : "")
          + (item.rejection_reason ? ` · ${item.rejection_reason}` : "");
        section.append(line);
        if (item.status === "pending") section.append(actionForm(item.id, "processing", "Mula Proses", []));
        if (item.status === "processing" && String(item.reviewer_id) === data.admin_id) {
          section.append(actionForm(item.id, "paid", "Rekod Bayaran Selesai", [
            ["reference", "Rujukan transaksi TNG", "text"], ["proof", "Bukti bayaran TNG", "file"]]));
        }
        if (item.status === "pending" || (item.status === "processing" && String(item.reviewer_id) === data.admin_id)) {
          section.append(actionForm(item.id, "rejected", "Tolak Tuntutan", [["reason", "Sebab penolakan", "text"]]));
        }
        if (item.status === "paid") {
          const proof = document.createElement("a");
          proof.href = `/api/web/admin/affiliate/claims/${item.id}/proof`;
          proof.textContent = "Muat Turun Bukti Bayaran";
          section.append(proof);
        }
        adminList.append(section);
      }
    } catch (error) {
      admin.hidden = true;
      adminList.replaceChildren();
      adminStatus.textContent = error.message;
    }
  }
  get("web-admin-tab")?.addEventListener("click", () => updateAdmin());
  get("affiliate-admin-refresh").addEventListener("click", () => updateAdmin());
  filter.addEventListener("change", () => updateAdmin());
  more.addEventListener("click", () => { page += 1; void updateAdmin(true); });
  void update();
  tab.addEventListener("click", update);
  window.cikgulajuReferralInit = () => update();
})();
