"use strict";
(() => {
  const emailPanel = document.getElementById("email-auth-panel");
  const emailStatus = document.getElementById("email-auth-status");
  const linkPanel = document.getElementById("email-link-section");
  const linkStatus = document.getElementById("email-link-status");
  const passwordChangeForm = document.getElementById("email-password-change-form");

  async function postJson(path, payload) {
    const response = await fetch(path, {
      method: "POST",
      credentials: "same-origin",
      cache: "no-store",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    });
    const data = await response.json().catch(() => ({}));
    if (!response.ok) throw new Error(data.error || "Permintaan belum berjaya. Cuba lagi.");
    return data;
  }

  function formCredentials(form) {
    const data = new FormData(form);
    return { email: String(data.get("email") || "").trim(),
             password: String(data.get("password") || "") };
  }

  fetch("/api/auth/email/capabilities", { cache: "no-store" })
    .then((response) => response.ok ? response.json() : null)
    .then((data) => { if (data?.email_auth_enabled === true) emailPanel.hidden = false; })
    .catch(() => {});

  document.getElementById("email-login-form")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    emailStatus.textContent = "Menyemak akaun…";
    try {
      await postJson("/api/auth/email/login", formCredentials(event.currentTarget));
      location.reload();
    } catch (error) {
      emailStatus.textContent = error.message;
    }
  });

  document.getElementById("email-signup-form")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    emailStatus.textContent = "Menghantar pautan pengesahan…";
    try {
      const data = await postJson("/api/auth/email/signup", formCredentials(event.currentTarget));
      emailStatus.textContent = data.message || "Semak e-mel untuk pengesahan.";
      event.currentTarget.reset();
    } catch (error) {
      emailStatus.textContent = error.message;
    }
  });

  document.getElementById("email-password-reset")?.addEventListener("click", async () => {
    const email = document.getElementById("email-login-address")?.value.trim() || "";
    emailStatus.textContent = "Menghantar arahan tetapan semula…";
    try {
      const data = await postJson("/api/auth/email/reset", { email });
      emailStatus.textContent = data.message || "Semak e-mel untuk arahan seterusnya.";
    } catch (error) {
      emailStatus.textContent = error.message;
    }
  });

  const recovery = new URLSearchParams(location.hash.slice(1));
  const recoveryToken = recovery.get("access_token");
  if (recovery.get("type") === "recovery" && recoveryToken) {
    document.getElementById("email-login-form").hidden = true;
    document.getElementById("email-signup-form").hidden = true;
    document.getElementById("email-signup-form").closest("details").hidden = true;
    passwordChangeForm.hidden = false;
    emailStatus.textContent = "Tetapkan kata laluan baharu untuk akaun anda.";
    history.replaceState(null, "", location.pathname + location.search);
    passwordChangeForm.addEventListener("submit", async (event) => {
      event.preventDefault();
      emailStatus.textContent = "Mengemas kini kata laluan…";
      try {
        const password = document.getElementById("email-password-change").value;
        const data = await postJson("/api/auth/email/password", {
          access_token: recoveryToken, password,
        });
        emailStatus.textContent = data.message || "Kata laluan berjaya dikemas kini.";
        passwordChangeForm.hidden = true;
        document.getElementById("email-login-form").hidden = false;
      } catch (error) {
        emailStatus.textContent = error.message;
      }
    });
  }

  document.getElementById("email-link-form")?.addEventListener("submit", async (event) => {
    event.preventDefault();
    linkStatus.textContent = "Mengesahkan dan memautkan e-mel…";
    try {
      const data = await postJson("/api/auth/email/link", formCredentials(event.currentTarget));
      linkStatus.textContent = data.message || "Permintaan pemautan e-mel diterima.";
      if (data.linked) event.currentTarget.hidden = true;
      else event.currentTarget.reset();
    } catch (error) {
      linkStatus.textContent = error.message;
    }
  });

  async function showEmailLinkStatus() {
    if (!linkPanel) return;
    try {
      const session = await fetch("/api/auth/telegram/session", {
        credentials: "same-origin", cache: "no-store",
      });
      if (!session.ok) return;
      const result = await fetch("/api/auth/email/link-status", {
        credentials: "same-origin", cache: "no-store",
      });
      const data = await result.json().catch(() => ({}));
      if (!result.ok || data.can_link === false && data.linked !== true) return;
      linkPanel.hidden = false;
      if (data.linked) {
        document.getElementById("email-link-form").hidden = true;
        linkStatus.textContent = "E-mel dipautkan: " + data.email;
      } else if (data.pending) {
        document.getElementById("email-link-form").hidden = true;
        linkStatus.textContent = "Pautan menunggu pengesahan. Semak e-mel anda.";
      }
    } catch (_) {
      // Login and account functions remain usable when this optional panel is offline.
    }
  }
  void showEmailLinkStatus();
})();
