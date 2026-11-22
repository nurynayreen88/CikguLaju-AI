/* CikguLaju private analytics: server-authorized aggregate data only.
 * This script has no privileged credentials or raw user identity access.
 */
(function () {
  "use strict";
  const tab = document.getElementById("web-admin-tab");
  const status = document.getElementById("web-admin-status");
  const updated = document.getElementById("web-admin-updated");
  const refresh = document.getElementById("web-admin-refresh");
  const view = document.getElementById("view-admin");
  if (!tab || !view || !status || !updated || !refresh) return;
  tab.hidden = true;
  view.hidden = true;
  let busy = false;

  // Keep a dedicated refresh control with the user registration metrics.
  const registrationMetric = document.getElementById("web-admin-new-users-30d");
  const registrationCard = registrationMetric && registrationMetric.closest(".admin-stats-card");
  const statsGrid = view.querySelector(".admin-stats-grid");
  if (registrationCard && statsGrid) {
    const refreshRow = document.createElement("div");
    refreshRow.className = "admin-users-refresh-row";
    refreshRow.style.gridColumn = "1 / -1";
    refreshRow.style.padding = "0 0 4px";
    refresh.textContent = "🔄 Muat Semula Analisis Pengguna";
    refresh.classList.add("profile-refresh");
    refreshRow.appendChild(refresh);
    registrationCard.insertAdjacentElement("afterend", refreshRow);
  }

  const text = (id, value) => {
    const node = document.getElementById(id);
    if (node) node.textContent = value;
  };
  const number = (value) =>
    Number.isSafeInteger(value) && value >= 0 ? value.toLocaleString("ms-MY") : "—";

  function show(data) {
    text("web-admin-users", number(data.registered_users));
    text("web-admin-new-users-today", number(data.new_users_today));
    text("web-admin-new-users-7d", number(data.new_users_7d));
    text("web-admin-new-users-30d", number(data.new_users_30d));
    text("web-admin-rakan", number(data.rakan_pembangun));
    text("web-admin-today", number(data.users_today));
    text("web-admin-week", number(data.users_7d));
    text("web-admin-month", number(data.users_30d));
    text("web-admin-credits", number(data.trial_credit_debits));
    text("web-admin-rph", number(data.confirmed_rph_records));
    const coverage = data.coverage || {};
    if (data.tracking_status === "not_started") {
      status.textContent =
        "Perekodan login Web belum bermula. Tanda — bukan bermaksud tiada pengguna log masuk.";
    } else if (data.tracking_status === "event_limit") {
      status.textContent =
        "Terlalu banyak rekod untuk dikira dengan tepat. Angka pengguna aktif disembunyikan sehingga kaedah agregat disediakan.";
    } else {
      const incomplete = [
        ["today", "hari ini"],
        ["last_7_days", "7 hari"],
        ["last_30_days", "30 hari"]
      ].filter(([key]) => coverage[key] !== true).map(([, label]) => label);
      status.textContent = incomplete.length
        ? "Data log masuk bagi " + incomplete.join(", ") +
          " belum merangkumi seluruh tempoh. Statistik hanya mencerminkan aktiviti sejak perekodan bermula."
        : "Pengguna aktif ialah bilangan akaun berbeza yang log masuk melalui Web dalam tempoh ditunjukkan.";
    }
    const rphNote = data.rph_coverage === "not_instrumented"
      ? "Jumlah keseluruhan RPH belum dapat disahkan daripada ledger sedia ada."
      : "Rekod penghantaran RPH ini mungkin belum merangkumi semua janaan lama dan berbayar.";
    text("web-admin-rph-note", rphNote +
         " Penggunaan kredit percubaan ialah transaksi debit, bukan jumlah semua RPH.");
    try {
      updated.textContent = "Dikemas kini: " +
        new Intl.DateTimeFormat("ms-MY", {
          timeZone: "Asia/Kuala_Lumpur", dateStyle: "medium", timeStyle: "short"
        }).format(new Date(data.generated_at));
    } catch (_) {
      updated.textContent = "Maklumat kemas kini tidak tersedia.";
    }
  }

  async function load() {
    if (busy) return;
    busy = true;
    refresh.disabled = true;
    try {
      const res = await fetch("/api/web/admin/usage", {
        method: "GET", credentials: "same-origin", cache: "no-store", redirect: "error"
      });
      if (res.status === 401 || res.status === 403) {
        tab.hidden = true;
        document.getElementById("view-admin").hidden = true;
        return;
      }
      if (!res.ok) throw Error("Analisis admin belum tersedia (HTTP " + res.status + ").");
      const result = await res.json();
      if (!result || !Number.isInteger(result.registered_users))
        throw Error("Format analisis tidak lengkap.");
      tab.hidden = false;
      show(result);
    } catch (error) {
      status.textContent = error.message || "Analisis tidak dapat dimuatkan. Cuba muat semula.";
    } finally {
      busy = false;
      refresh.disabled = false;
    }
  }

  refresh.addEventListener("click", () => void load());
  tab.addEventListener("click", () => void load());
  // Called only after the regular Telegram Widget session has been checked.
  window.cikgulajuAdminInit = () => load();
  // Cover the case where session verification finishes before this asset loads.
  if (document.getElementById("workspace")?.hidden === false) void load();
})();

(function () {
  "use strict";
  const get = id => document.getElementById(id);
  const panel = get("admin-payments");
  if (!panel) return;
  const status = get("admin-payment-status");
  const filter = get("admin-payment-filter");
  const list = get("admin-payment-list");
  const previous = get("admin-payment-prev");
  const next = get("admin-payment-next");
  const dialog = get("admin-payment-dialog");
  const detailStatus = get("admin-payment-dialog-status");
  const proof = get("admin-payment-proof");
  const actions = get("admin-payment-decision");
  const checked = get("admin-payment-confirm");
  const approve = get("admin-payment-approve");
  const reject = get("admin-payment-reject");
  const close = get("admin-payment-close");
  const tab = get("web-admin-tab");
  const date = new Intl.DateTimeFormat("ms-MY", {
    timeZone: "Asia/Kuala_Lumpur", dateStyle: "medium", timeStyle: "short"
  });
  const api = "/api/web/admin/payments";
  let page = 0;
  let revision = 0;
  let receiptRevision = 0;
  let receiptUrl;
  let selected;
  let reviewing = false;
  const options = {credentials:"same-origin", cache:"no-store", redirect:"error"};

  function ageLabel(raw) {
    const minutes = Math.floor((Date.now() - Date.parse(raw)) / 60000);
    if (minutes >= 360) return "Menunggu 6 jam atau lebih";
    if (minutes >= 60) return "Menunggu " + Math.floor(minutes / 60) + " jam";
    if (minutes >= 15) return "Menunggu " + minutes + " minit";
    return "";
  }

  function syncActions() {
    approve.disabled = reject.disabled = reviewing || !checked.checked;
    close.disabled = reviewing;
  }

  function clearProof() {
    receiptRevision++;
    if (receiptUrl) URL.revokeObjectURL(receiptUrl);
    receiptUrl = undefined;
    proof.replaceChildren();
  }

  async function openReceipt(item) {
    if (reviewing) return;
    clearProof();
    const ticket = receiptRevision;
    selected = item;
    checked.checked = false;
    actions.hidden = true;
    syncActions();
    get("admin-payment-dialog-title").textContent = "Resit #" + item.id + " · " + item.name;
    detailStatus.textContent = "Memuatkan resit…";
    dialog.showModal();
    try {
      const response = await fetch(api + "/" + item.id + "/receipt", options);
      if (!response.ok) throw Error("Resit belum dapat dibuka. Cuba semula.");
      const blob = await response.blob();
      if (ticket !== receiptRevision) return;
      if (blob.type.startsWith("image/")) {
        receiptUrl = URL.createObjectURL(blob);
        const image = document.createElement("img");
        image.src = receiptUrl;
        image.alt = "Resit bayaran #" + item.id;
        image.style.maxWidth = "100%";
        image.style.maxHeight = "55vh";
        image.style.objectFit = "contain";
        proof.append(image);
      } else {
        const link = document.createElement("a");
        link.href = api + "/" + item.id + "/receipt";
        link.target = "_blank";
        link.rel = "noopener";
        link.textContent = "Buka resit PDF";
        proof.append(link);
      }
      detailStatus.textContent = item.package + " · RM" + item.amount;
      actions.hidden = !item.can_review;
    } catch (error) {
      if (ticket === receiptRevision) detailStatus.textContent = error.message;
    }
  }

  async function review(decision) {
    if (reviewing || !checked.checked || !selected?.can_review) return;
    reviewing = true;
    syncActions();
    const item = selected;
    detailStatus.textContent = "Menyimpan keputusan…";
    try {
      const response = await fetch(api + "/" + item.id + "/review", {...options,
        method:"POST", headers:{"Content-Type":"application/json"},
        body:JSON.stringify({payer:item.user_id, receipt_at:item.received, decision})});
      const result = await response.json();
      if (!response.ok || result.status !== decision) throw Error(result.error || "Semakan belum dapat disahkan.");
      dialog.close();
      await load();
      status.textContent = decision === "approved" ? "Bayaran #" + item.id + " disahkan." : "Bayaran #" + item.id + " ditolak.";
    } catch (error) {
      detailStatus.textContent = error.message || "Semakan belum dapat disahkan. Muat semula senarai.";
    } finally {
      reviewing = false;
      checked.checked = false;
      syncActions();
    }
  }

  async function load() {
    const ticket = ++revision;
    const state = filter.value;
    status.textContent = "Memuatkan bayaran…";
    list.replaceChildren();
    previous.hidden = next.hidden = true;
    try {
      const response = await fetch(api + "?" + new URLSearchParams({status:state, page}), options);
      if (ticket !== revision) return;
      if (response.status === 401 || response.status === 403) { panel.hidden = true; return; }
      if (!response.ok) throw Error("Senarai bayaran belum dapat dimuatkan. Cuba semula.");
      const data = await response.json();
      if (ticket !== revision) return;
      panel.hidden = false;
      for (const item of data.items) {
        const row = document.createElement("li");
        const heading = document.createElement("strong");
        heading.textContent = item.name + " · #" + item.id;
        row.append(heading);
        const detail = document.createElement("p");
        const stamp = state === "pending" ? item.received || item.submitted : item.reviewed || item.submitted;
        const label = state === "pending" ? ageLabel(item.received || item.submitted) : "";
        const formatted = Number.isFinite(Date.parse(stamp)) ? date.format(new Date(stamp)) : "";
        detail.textContent = [item.package, "RM" + item.amount, formatted, label].filter(Boolean).join(" · ");
        row.append(detail);
        if (item.has_receipt) {
          const button = document.createElement("button");
          button.type = "button";
          button.textContent = "Semak Resit";
          button.addEventListener("click", () => void openReceipt(item));
          row.append(button);
        } else {
          row.append(document.createTextNode("Resit belum tersedia"));
        }
        list.append(row);
      }
      status.textContent = data.items.length ? "" : (state === "pending" ? "Tiada bayaran menunggu semakan." : "Tiada rekod dalam penapis ini.");
      previous.hidden = page === 0;
      next.hidden = !data.more;
    } catch (error) {
      if (ticket === revision) {
        panel.hidden = false;
        status.textContent = error.message || "Senarai bayaran belum dapat dimuatkan.";
      }
    }
  }

  close.addEventListener("click", () => dialog.close());
  dialog.addEventListener("cancel", event => { if (reviewing) event.preventDefault(); });
  dialog.addEventListener("close", clearProof);
  checked.addEventListener("change", syncActions);
  approve.addEventListener("click", () => void review("approved"));
  reject.addEventListener("click", () => void review("rejected"));
  filter.addEventListener("change", () => { page = 0; void load(); });
  get("admin-payment-refresh").addEventListener("click", () => { page = 0; void load(); });
  previous.addEventListener("click", () => { if (page > 0) page--; void load(); });
  next.addEventListener("click", () => { page++; void load(); });
  window.cikgulajuPaymentsAdminLoad = () => { page = 0; return load(); };
  window.cikgulajuOpenPaymentsAdmin = async () => {
    await window.cikgulajuAdminInit?.();
    if (!tab.hidden) tab.click();
  };
})();


/* Admin-only user directory: server controls authorization and filtering.
 * No raw account UUID, passwords or service credentials in this script.
 */
(function () {
  "use strict";
  const get = id => document.getElementById(id);
  const panel = get("admin-users-directory");
  if (!panel) return;
  const search = get("admin-users-search");
  const filter = get("admin-users-filter");
  const apply = get("admin-users-apply");
  const refresh = get("admin-users-refresh");
  const status = get("admin-users-status");
  const list = get("admin-users-list");
  const prev = get("admin-users-prev");
  const next = get("admin-users-next");
  const pageLabel = get("admin-users-page");
  const date = new Intl.DateTimeFormat("ms-MY", {
    timeZone: "Asia/Kuala_Lumpur", year: "numeric", month: "short",
    day: "numeric", hour: "2-digit", minute: "2-digit"
  });
  const accessLabels = {
    free: "Free",
    rakan: "Rakan Pembangun",
    langganan: "Langganan"
  };
  let page = 0;
  let serial = 0;
  let loaded = false;
  let appliedSearch = "";
  let appliedFilter = "all";

  const formatDate = value => {
    if (!value || !Number.isFinite(Date.parse(value))) return "Belum direkodkan";
    return date.format(new Date(value));
  };
  function itemValue(label, value, parent) {
    const dt = document.createElement("dt");
    dt.textContent = label;
    const dd = document.createElement("dd");
    dd.textContent = value;
    parent.append(dt, dd);
  }
  function renderItem(item) {
    const li = document.createElement("li");
    const header = document.createElement("div");
    header.className = "admin-user-top";
    const id = document.createElement("strong");
    id.className = "admin-user-identity";
    if (item.account_type === "email") {
      id.textContent = item.email || "Akaun e-mel";
    } else {
      id.textContent = item.telegram_id ? "Telegram · " + item.telegram_id : "Akaun Telegram";
    }
    const badge = document.createElement("span");
    badge.className = "admin-user-badge";
    badge.textContent = accessLabels[item.access_status] || "Status tidak tersedia";
    header.append(id, badge);
    li.append(header);
    if (item.display_name && item.display_name !== "Pengguna E-mel"
        && item.display_name !== "Pengguna Telegram") {
      const name = document.createElement("p");
      name.className = "admin-user-name";
      name.textContent = item.display_name;
      li.append(name);
    }
    const details = document.createElement("dl");
    if (item.account_type === "telegram" && item.email) {
      itemValue("E-mel pautan", item.email, details);
    }
    itemValue("Daftar", formatDate(item.registered_at), details);
    itemValue("Login terakhir", formatDate(item.last_login_at), details);
    if (item.access_status === "langganan" && item.subscription_expires_at) {
      itemValue("Tamat", formatDate(item.subscription_expires_at), details);
    }
    if (item.access_status === "free" && Number.isInteger(item.trial_remaining)) {
      itemValue("RPH percuma", item.trial_remaining + " baki", details);
    }
    li.append(details);
    return li;
  }

  async function load() {
    if (!panel.open) return;
    const ticket = ++serial;
    apply.disabled = refresh.disabled = prev.disabled = next.disabled = true;
    status.textContent = "Memuatkan senarai pengguna…";
    list.replaceChildren();
    try {
      const params = new URLSearchParams({
        status: appliedFilter, search: appliedSearch, page: String(page)
      });
      const response = await fetch("/api/web/admin/users?" + params.toString(), {
        method: "GET", credentials: "same-origin", cache: "no-store", redirect: "error"
      });
      if (ticket !== serial) return;
      if (response.status === 401 || response.status === 403) {
        throw new Error("Akses admin diperlukan. Sila log masuk semula.");
      }
      if (!response.ok) throw new Error("Senarai pengguna tidak dapat dimuatkan (HTTP " +
                                          response.status + ").");
      const data = await response.json();
      if (ticket !== serial) return;
      if (!data || !Array.isArray(data.items) || !Number.isSafeInteger(data.total)
          || data.page !== page) throw new Error("Respons senarai pengguna tidak sah.");
      for (const item of data.items) list.append(renderItem(item));
      const start = data.total === 0 ? 0 : page * 20 + 1;
      const end = Math.min(data.total, page * 20 + data.items.length);
      status.textContent = data.total === 0
        ? "Tiada pengguna sepadan dengan carian ini."
        : "Memaparkan " + start + "–" + end + " daripada " +
          data.total.toLocaleString("ms-MY") + " pengguna.";
      pageLabel.textContent = "Halaman " + (page + 1);
      prev.hidden = page === 0;
      next.hidden = data.more !== true;
      loaded = true;
    } catch (error) {
      if (ticket === serial) {
        status.textContent = error.message || "Senarai pengguna tidak dapat dimuatkan.";
        prev.hidden = next.hidden = true;
      }
    } finally {
      if (ticket === serial) {
        apply.disabled = refresh.disabled = prev.disabled = next.disabled = false;
      }
    }
  }

  function applyFilters() {
    appliedSearch = search.value.trim().slice(0, 100);
    appliedFilter = filter.value;
    page = 0;
    void load();
  }
  panel.addEventListener("toggle", () => {
    if (panel.open && !loaded) void load();
  });
  apply.addEventListener("click", applyFilters);
  search.addEventListener("keydown", event => {
    if (event.key === "Enter") {
      event.preventDefault();
      applyFilters();
    }
  });
  filter.addEventListener("change", applyFilters);
  refresh.addEventListener("click", () => void load());
  prev.addEventListener("click", () => { if (page > 0) { page--; void load(); } });
  next.addEventListener("click", () => { page++; void load(); });
  window.cikgulajuUsersAdminLoad = () => {
    if (panel.open) void load();
  };
})();
