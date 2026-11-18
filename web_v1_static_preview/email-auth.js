(() => {
  "use strict";

  async function postJson(path, payload) {
    const response = await fetch(path, {
      method: "POST",
      credentials: "same-origin",
      headers: { "Content-Type": "application/json", "Accept": "application/json" },
      body: JSON.stringify(payload)
    });
    const data = await response.json().catch(() => ({}));
    return { response, data };
  }

  function credentials(emailInput, passwordInput) {
    const email = emailInput && emailInput.value.trim();
    const password = passwordInput && passwordInput.value;
    if (!email || !password) {
      throw new Error("Masukkan alamat emel dan kata laluan.");
    }
    if (password.length < 8 || new TextEncoder().encode(password).length > 72) {
      throw new Error("Kata laluan perlu 8–72 aksara UTF-8.");
    }
    return { email, password };
  }

  function setBusy(buttons, busy) {
    buttons.forEach((button) => {
      if (button) button.disabled = busy;
    });
  }

  const loginEmail = document.getElementById("email-login-address");
  const loginPassword = document.getElementById("email-login-password");
  const loginStatus = document.getElementById("email-login-status");
  const loginButton = document.getElementById("email-login-button");
  const registerButton = document.getElementById("email-register-button");

  async function runLoginAction(path, button) {
    if (!loginStatus) return;
    setBusy([loginButton, registerButton], true);
    loginStatus.textContent = "Sedang menyemak maklumat…";
    try {
      const body = credentials(loginEmail, loginPassword);
      const { response, data } = await postJson(path, body);
      if (response.status === 202 && data.confirmation_required) {
        loginStatus.textContent = data.message ||
          "Semak emel untuk pengesahan. Selepas itu, kembali ke sini dan log masuk.";
        return;
      }
      if (!response.ok) {
        throw new Error(data.error || "Permintaan tidak berjaya. Cuba lagi.");
      }
      if (data.authenticated) {
        loginStatus.textContent = "Berjaya. Membuka akaun…";
        window.location.reload();
        return;
      }
      loginStatus.textContent = data.message || "Permintaan diterima.";
    } catch (error) {
      loginStatus.textContent = error instanceof Error
        ? error.message : "Sambungan tergendala. Cuba lagi.";
    } finally {
      setBusy([loginButton, registerButton], false);
    }
  }

  if (loginButton) {
    loginButton.addEventListener("click", () => {
      runLoginAction("/api/auth/email/login", loginButton);
    });
  }
  if (registerButton) {
    registerButton.addEventListener("click", () => {
      runLoginAction("/api/auth/email/register", registerButton);
    });
  }

  const accountView = document.getElementById("view-account");
  const accountHeading = document.getElementById("view-account-heading");
  if (accountView && accountHeading && !document.getElementById("email-link-card")) {
    const card = document.createElement("section");
    card.id = "email-link-card";
    card.className = "email-link-card";
    card.setAttribute("aria-labelledby", "email-link-heading");
    card.innerHTML = [
      '<h3 id="email-link-heading">Pautkan Emel ke Akaun Telegram</h3>',
      '<p>Pautkan emel supaya anda boleh log masuk tanpa Telegram. Baki, akses dan had janaan akaun ini kekal sama.</p>',
      '<label for="email-link-address">Alamat emel</label>',
      '<input id="email-link-address" type="email" autocomplete="email" maxlength="254" required>',
      '<label for="email-link-password">Kata laluan</label>',
      '<input id="email-link-password" type="password" autocomplete="new-password" minlength="8" maxlength="72" required>',
      '<button id="email-link-button" type="button">Pautkan Emel</button>',
      '<p id="email-link-status" class="notice" role="status" aria-live="polite"></p>'
    ].join("");
    accountHeading.insertAdjacentElement("afterend", card);

    const linkButton = document.getElementById("email-link-button");
    const linkEmail = document.getElementById("email-link-address");
    const linkPassword = document.getElementById("email-link-password");
    const linkStatus = document.getElementById("email-link-status");
    linkButton.addEventListener("click", async () => {
      setBusy([linkButton], true);
      linkStatus.textContent = "Sedang mengesahkan emel…";
      try {
        const body = credentials(linkEmail, linkPassword);
        const { response, data } = await postJson("/api/auth/email/link", body);
        if (response.status === 202 && data.confirmation_required) {
          linkStatus.textContent = data.message ||
            "Semak emel untuk pengesahan. Selepas itu, log masuk Telegram dan ulangi pautan.";
          return;
        }
        if (!response.ok) {
          throw new Error(data.error || "Pautan emel tidak berjaya.");
        }
        linkStatus.textContent =
          "Emel berjaya dipautkan. Selepas ini anda boleh log masuk dengan emel dan kata laluan.";
        linkPassword.value = "";
      } catch (error) {
        linkStatus.textContent = error instanceof Error
          ? error.message : "Sambungan tergendala. Cuba lagi.";
      } finally {
        setBusy([linkButton], false);
      }
    });
  }
})();
