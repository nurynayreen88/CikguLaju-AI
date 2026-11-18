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
  const forgotButton = document.getElementById("email-forgot-button");

  async function runLoginAction(path, button) {
    if (!loginStatus) return;
    setBusy([loginButton, registerButton, forgotButton], true);
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
      setBusy([loginButton, registerButton, forgotButton], false);
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

  if (forgotButton) {
    forgotButton.addEventListener("click", async () => {
      if (!loginStatus) return;
      const email = loginEmail && loginEmail.value.trim();
      if (!email) {
        loginStatus.textContent = "Masukkan alamat emel dahulu, kemudian tekan Lupa kata laluan?.";
        if (loginEmail) loginEmail.focus();
        return;
      }
      setBusy([loginButton, registerButton, forgotButton], true);
      loginStatus.textContent = "Sedang meminta pautan pemulihan…";
      try {
        const { response, data } = await postJson("/api/auth/email/recover", { email });
        if (!response.ok) throw new Error(data.error || "Emel pemulihan belum dapat diminta.");
        loginStatus.textContent = data.message ||
          "Jika akaun dengan emel ini wujud, pautan pemulihan akan dihantar.";
      } catch (error) {
        loginStatus.textContent = error instanceof Error
          ? error.message : "Sambungan tergendala. Cuba lagi.";
      } finally {
        setBusy([loginButton, registerButton, forgotButton], false);
      }
    });
  }

  function setupPasswordRecovery() {
    const params = new URLSearchParams(window.location.hash.slice(1));
    const recovery = params.get("type") === "recovery";
    const accessToken = params.get("access_token") || "";
    if (!recovery) return;
    history.replaceState(null, "", location.pathname + location.search);
    const box = document.getElementById("email-auth-login");
    if (!box) return;
    const panel = document.createElement("section");
    panel.className = "email-auth-reset";
    panel.setAttribute("aria-labelledby", "email-reset-heading");
    if (!accessToken) {
      panel.innerHTML = [
        '<h2 id="email-reset-heading">Pautan pemulihan tidak lengkap</h2>',
        '<p>Minta pautan Lupa kata laluan? yang baharu dan buka pautan itu pada peranti ini.</p>',
        '<button id="email-reset-back" type="button">Kembali ke log masuk</button>'
      ].join("");
      box.replaceChildren(panel);
      document.getElementById("email-reset-back").addEventListener("click", () => {
        location.reload();
      });
      return;
    }
    panel.innerHTML = [
      '<h2 id="email-reset-heading">Tetapkan kata laluan baharu</h2>',
      '<p>Pilih kata laluan sekurang-kurangnya 8 aksara.</p>',
      '<label for="email-reset-password">Kata laluan baharu</label>',
      '<input id="email-reset-password" type="password" autocomplete="new-password" minlength="8" maxlength="72" required>',
      '<label for="email-reset-confirm">Ulang kata laluan baharu</label>',
      '<input id="email-reset-confirm" type="password" autocomplete="new-password" minlength="8" maxlength="72" required>',
      '<button id="email-reset-submit" type="button">Simpan Kata Laluan Baharu</button>',
      '<p id="email-reset-status" class="notice" role="status" aria-live="polite"></p>'
    ].join("");
    box.replaceChildren(panel);
    const passwordInput = document.getElementById("email-reset-password");
    const confirmInput = document.getElementById("email-reset-confirm");
    const submit = document.getElementById("email-reset-submit");
    const status = document.getElementById("email-reset-status");
    submit.addEventListener("click", async () => {
      const password = passwordInput.value;
      if (password.length < 8 || new TextEncoder().encode(password).length > 72) {
        status.textContent = "Kata laluan baharu perlu 8–72 aksara UTF-8.";
        passwordInput.focus();
        return;
      }
      if (password !== confirmInput.value) {
        status.textContent = "Kedua-dua kata laluan tidak sama.";
        confirmInput.focus();
        return;
      }
      submit.disabled = true;
      status.textContent = "Sedang mengemas kini kata laluan…";
      try {
        const { response, data } = await postJson("/api/auth/email/reset", {
          access_token: accessToken,
          password
        });
        if (!response.ok) throw new Error(data.error || "Kata laluan belum dapat dikemas kini.");
        panel.innerHTML = [
          '<h2 id="email-reset-heading">Kata laluan berjaya ditukar</h2>',
          '<p>Log masuk semula menggunakan kata laluan baharu anda.</p>',
          '<button id="email-reset-back" type="button">Kembali ke log masuk</button>'
        ].join("");
        document.getElementById("email-reset-back").addEventListener("click", () => {
          location.reload();
        });
      } catch (error) {
        status.textContent = error instanceof Error
          ? error.message : "Sambungan tergendala. Cuba lagi.";
        submit.disabled = false;
      }
    });
    passwordInput.focus();
  }

  setupPasswordRecovery();

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
