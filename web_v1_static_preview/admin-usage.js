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
