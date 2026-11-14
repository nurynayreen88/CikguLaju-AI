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
  const account = get("affiliate-account-number");
  const confirm = get("affiliate-confirm");
  const amount = get("affiliate-amount");
  const claimStatus = get("affiliate-status");
  const history = get("affiliate-history");
  const admin = get("affiliate-admin");
  const filter = get("affiliate-admin-filter");
  const adminStatus = get("affiliate-admin-status");
  const adminList = get("affiliate-admin-list");
  const adminClaims = get("affiliate-admin-claims");
  const memberFilter = get("affiliate-admin-member-filter");
  const selectedMember = get("affiliate-admin-selected-member");
  const membersFilter = get("affiliate-members-filter");
  const membersList = get("affiliate-members-list");
  const membersStatus = get("affiliate-members-status");
  const membersPrev = get("affiliate-members-prev");
  const membersNext = get("affiliate-members-next");
  const more = get("affiliate-admin-more");
  if (!box || !status || !linkInput || !copy || !share || !tab || !view || !claimPanel || !admin) return;

  const labels = {pending:"Menunggu", processing:"Dalam Proses", paid:"Dibayar", rejected:"Ditolak"};
  const money = value => Number(value).toLocaleString("en-MY", {minimumFractionDigits:2, maximumFractionDigits:2});
  const date = value => new Date(value).toLocaleString("ms-MY", {timeZone:"Asia/Kuala_Lumpur"});
  const deepLink = new URLSearchParams(window.location.search).get("affiliate") === "1";
  let openFromTelegram = deepLink;
  let savedAccount = "";
  let available = 0;
  let requestKey;
  let requestIdentity;
  let page = 0;
  let membersPage = 0;
  let membersRequest = 0;
  let adminRequest = 0;
  let memberId = "";
  let claimRequest = 0;
  let updateRequest = 0;
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
    claimRequest += 1;
    tab.hidden = true;
    box.hidden = true;
    claimPanel.hidden = true;
    linkInput.value = "";
    account.value = savedAccount = "";
    history.replaceChildren();
    confirm.checked = false;
    if (!view.hidden) document.querySelector('[data-web-view="today"]')?.click();
    view.hidden = true;
  }
  function syncSubmit() {
    get("affiliate-submit").disabled = submitting || !savedAccount || account.value !== savedAccount || !confirm.checked || available < 10;
  }
  function claimDetails(row) {
    return (row.paid_at ? ` · Dibayar pada ${date(row.paid_at)}` : "")
      + (row.payment_reference ? ` · Rujukan ${row.payment_reference}` : "")
      + (row.rejection_reason ? ` · Sebab penolakan ${row.rejection_reason}` : "");
  }
  function showClaims(data) {
    claimPanel.hidden = !data.open;
    if (!data.open) return;
    const nextAccount = data.account_number || "";
    if (account.value === savedAccount) account.value = nextAccount;
    if (nextAccount !== savedAccount) confirm.checked = false;
    savedAccount = nextAccount;
    available = Number(data.available);
    get("affiliate-available").textContent = money(available);
    get("affiliate-balance").textContent = money(data.balance);
    get("affiliate-reserved").textContent = money(data.reserved);
    get("affiliate-paid").textContent = money(data.paid);
    amount.max = String(available);
    claimForm.hidden = !savedAccount || available < 10;
    history.replaceChildren();
    for (const row of data.claims) {
      const li = document.createElement("li");
      li.textContent = `Dimohon pada ${date(row.requested_at)} · RM${money(row.points)} · ${labels[row.status]}`
        + claimDetails(row);
      history.append(li);
    }
    if (!data.claims.length) {
      const li = document.createElement("li");
      li.textContent = "Belum ada tuntutan.";
      history.append(li);
    }
    syncSubmit();
  }
  async function refreshClaims() {
    const revision = ++claimRequest;
    try {
      const details = await api("/api/web/affiliate");
      if (revision !== claimRequest) return;
      showClaims(details);
      return details;
    } catch (_) {
      if (revision === claimRequest) {
        claimPanel.hidden = true;
        for (const id of ["affiliate-balance", "affiliate-reserved", "affiliate-paid"]) get(id).textContent = "—";
      }
    }
  }
  async function update() {
    const revision = ++updateRequest;
    try {
      const data = await api("/api/web/referral");
      if (revision !== updateRequest) return;
      if (data.enabled !== true || typeof data.link !== "string" ||
          !data.link.startsWith("https://cikgulaju-web.onrender.com/?ref=")) { revoke(); return; }
      linkInput.value = data.link;
      get("web-referral-signups").textContent = String(data.registered);
      get("web-referral-paid").textContent = String(data.paid);
      box.hidden = false;
      status.textContent = "Mata dikreditkan selepas bayaran pertama disahkan.";
      tab.hidden = false;
      const details = await refreshClaims();
      if (revision !== updateRequest) return;
      if (details?.open) status.textContent = `Ganjaran ${details.rate}% bagi bayaran pertama yang disahkan.`;
      if (openFromTelegram) {
        openFromTelegram = false;
        tab.click();
      }
    } catch (_) { if (revision === updateRequest) revoke(); }
  }

  account.addEventListener("input", () => { confirm.checked = false; syncSubmit(); });
  confirm.addEventListener("change", syncSubmit);
  walletForm.addEventListener("submit", async event => {
    event.preventDefault();
    const button = get("affiliate-save-wallet");
    button.disabled = true;
    try {
      await api("/api/web/affiliate/wallet", jsonPost({account_number:account.value, confirmed:confirm.checked}));
      account.value = savedAccount;
      await update();
      claimStatus.textContent = "Nombor akaun TNG eWallet disimpan.";
    } catch (error) { claimStatus.textContent = error.message; }
    finally { button.disabled = false; }
  });
  claimForm.addEventListener("submit", async event => {
    event.preventDefault();
    if (get("affiliate-submit").disabled) return;
    const identity = `${savedAccount}/${amount.value}`;
    if (requestIdentity !== identity) {
      requestIdentity = identity;
      requestKey = crypto.randomUUID();
    }
    submitting = true;
    syncSubmit();
    try {
      await api("/api/web/affiliate/claims", jsonPost({account_number:savedAccount, confirmed:confirm.checked, points:amount.value, key:requestKey}));
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
        if (adminList.contains(form)) filter.value = action;
        await Promise.all([updateAdmin(), updateMembers(membersPage)]);
        adminStatus.textContent = "Status tuntutan dikemas kini.";
      } catch (error) { adminStatus.textContent = error.message; }
      finally { button.disabled = false; }
    });
    return form;
  }
  async function updateMembers(nextPage = membersPage) {
    const revision = ++membersRequest;
    const query = new URLSearchParams({page:String(nextPage), referral_status:membersFilter.value});
    membersPrev.disabled = membersNext.disabled = true;
    membersStatus.textContent = "Memuatkan senarai affiliate…";
    try {
      const data = await api(`/api/web/admin/affiliate/members?${query}`);
      if (revision !== membersRequest) return;
      membersPage = nextPage;
      admin.hidden = false;
      membersList.replaceChildren();
      for (const item of data.items) {
        const li = document.createElement("li");
        const name = [item.first_name, item.username && `@${item.username}`].filter(Boolean).join(" ");
        const heading = document.createElement("button");
        heading.type = "button";
        const identity = [name, `ID ${item.user_id}`].filter(Boolean).join(" · ");
        heading.textContent = identity;
        heading.setAttribute("aria-label", `Semak tuntutan ${identity}`);
        heading.addEventListener("click", () => {
          memberId = item.user_id;
          selectedMember.textContent = identity;
          memberFilter.hidden = false;
          filter.value = "all";
          filter.focus();
          void updateAdmin();
        });
        const referrals = document.createElement("div");
        referrals.textContent = `${item.registered_count} jemputan berdaftar · ${item.payment_count} bayaran disahkan`;
        const balances = document.createElement("div");
        balances.textContent = `${item.enabled ? "Aktif" : "Tidak aktif"} · Baki ${money(item.balance)} mata · Boleh dituntut ${money(item.available)} · Dalam tuntutan ${money(item.reserved)} · Dibayar ${money(item.paid)}`;
        li.append(heading, referrals, balances);
        membersList.append(li);
      }
      membersStatus.textContent = data.items.length ? `Halaman ${membersPage + 1}` : "Tiada affiliate bagi pilihan ini.";
      membersPrev.hidden = membersPage === 0;
      membersNext.hidden = !data.more;
    } catch (error) {
      if (revision !== membersRequest) return;
      membersList.replaceChildren();
      membersStatus.textContent = error.message;
      membersPrev.hidden = membersPage === 0;
      membersNext.hidden = true;
    } finally {
      if (revision === membersRequest) membersPrev.disabled = membersNext.disabled = false;
    }
  }
  async function updateAdmin(append = false) {
    const revision = ++adminRequest;
    const requestedPage = append ? page + 1 : 0;
    const query = new URLSearchParams({status:filter.value, page:String(requestedPage)});
    if (memberId) query.set("user_id", memberId);
    more.disabled = true;
    if (!append) {
      adminList.replaceChildren();
      more.hidden = true;
      adminStatus.textContent = "Memuatkan tuntutan…";
    }
    try {
      const data = await api(`/api/web/admin/affiliate/claims?${query}`);
      if (revision !== adminRequest) return;
      page = requestedPage;
      adminClaims.hidden = !data.open;
      more.hidden = !data.more;
      adminStatus.textContent = data.items.length ? "" : "Tiada tuntutan bagi pilihan ini.";
      for (const item of data.items) {
        const section = document.createElement("section");
        section.className = "teacher-timetable-section";
        const line = document.createElement("p");
        line.textContent = `Akaun ${item.user_id} · Akaun TNG ${item.account_number_snapshot || "belum direkodkan"} · RM${money(item.points)} · Dimohon pada ${date(item.requested_at)} · ${labels[item.status]}`
          + claimDetails(item);
        section.append(line);
        if (item.status === "pending" && item.account_number_snapshot) {
          section.append(actionForm(item.id, "processing", "Mula Proses", []));
        }
        if (item.status === "pending" && !item.account_number_snapshot) {
          const notice = document.createElement("p");
          notice.textContent = "Tolak tuntutan lama ini supaya affiliate boleh masukkan nombor akaun TNG eWallet dan hantar semula.";
          section.append(notice);
        }
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
      if (revision === adminRequest) adminStatus.textContent = error.message;
    } finally {
      if (revision === adminRequest) more.disabled = false;
    }
  }
  function refreshAdmin() {
    void updateMembers();
    void updateAdmin();
  }
  get("web-admin-tab")?.addEventListener("click", refreshAdmin);
  get("affiliate-admin-refresh").addEventListener("click", refreshAdmin);
  get("affiliate-admin-clear-member").addEventListener("click", () => {
    memberId = "";
    memberFilter.hidden = true;
    filter.value = "pending";
    filter.focus();
    void updateAdmin();
  });
  membersFilter.addEventListener("change", () => {
    membersPage = 0;
    membersList.replaceChildren();
    void updateMembers();
  });
  membersPrev.addEventListener("click", () => updateMembers(membersPage - 1));
  membersNext.addEventListener("click", () => updateMembers(membersPage + 1));
  filter.addEventListener("change", () => updateAdmin());
  more.addEventListener("click", () => updateAdmin(true));
  void update();
  tab.addEventListener("click", update);
  function refreshVisibleBalance() {
    if (!document.hidden && !view.hidden && !tab.hidden && !submitting) void refreshClaims();
  }
  document.addEventListener("visibilitychange", refreshVisibleBalance);
  window.setInterval(refreshVisibleBalance, 30000);
  window.cikgulajuReferralInit = () => update();
})();
