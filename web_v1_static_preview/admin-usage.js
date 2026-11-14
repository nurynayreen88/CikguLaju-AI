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

  const text = (id, value) => {
    const node = document.getElementById(id);
    if (node) node.textContent = value;
  };
  const number = (value) =>
    Number.isSafeInteger(value) && value >= 0 ? value.toLocaleString("ms-MY") : "—";

  function show(data) {
    text("web-admin-users", number(data.registered_users));
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
