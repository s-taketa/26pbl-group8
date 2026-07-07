// static/js/main.js
// ログイン画面とダッシュボード画面の動的処理を担当する。

// HTMLエスケープ（XSS対策）
function esc(s) {
  return String(s == null ? "" : s)
    .replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;").replace(/'/g, "&#39;");
}

function badge(isEmergency) {
  return isEmergency
    ? '<span class="badge badge-fail">緊急</span>'
    : '<span class="badge badge-ok">通常</span>';
}

// ===================== ログ一覧の共通描画 =====================
// ログ1件のHTML（クリック可能・サムネイル付き）
function logItemHTML(r, i) {
  const thumb = r.image_url
    ? '<span class="log-thumb" style="background-image:url(\'' + r.image_url + '\')"></span>'
    : '<span class="log-thumb"></span>';
  return '<div class="log-item clickable" data-idx="' + i + '">' +
    thumb +
    '<span class="log-main">' +
      '<span class="log-q">' + esc(r.query) + '</span>' +
      '<span class="log-time">' + esc(r.timestamp) + ' ・ ' + badge(r.is_emergency) + '</span>' +
    '</span>' +
    '<span style="align-self:center;color:#b0bccd;">›</span>' +
  '</div>';
}

// タイムラインを描画し、各行クリックで詳細モーダルを開けるようにする
function renderTimeline(listEl, rows) {
  if (!Array.isArray(rows) || rows.length === 0) {
    listEl.innerHTML = '<div class="empty">履歴がまだありません</div>';
    return;
  }
  listEl.innerHTML = rows.map((r, i) => logItemHTML(r, i)).join("");
  listEl.querySelectorAll(".log-item").forEach(el => {
    el.addEventListener("click", () => openLogDetail(rows[+el.dataset.idx]));
  });
}

// 詳細モーダルの背景クリックで閉じる（多重登録防止）
function setupModalClose() {
  const modal = document.getElementById("logModal");
  if (modal && !modal._bound) {
    modal.addEventListener("click", e => { if (e.target.id === "logModal") closeLogDetail(); });
    modal._bound = true;
  }
}

// モーダル表示中は自動更新で裏のリストを書き換えない
function isLogModalOpen() {
  const m = document.getElementById("logModal");
  return m && m.style.display === "grid";
}

// ===================== ログイン画面（メール2段階認証対応） =====================
function initLogin() {
  const form = document.getElementById("loginForm");
  if (!form) return;

  const msg = document.getElementById("formMessage");
  const btn = document.getElementById("loginBtn");
  const idEl = document.getElementById("loginId");
  const pwEl = document.getElementById("password");
  const verifyForm = document.getElementById("verifyForm");
  const verifyBtn = document.getElementById("verifyBtn");
  const codeEl = document.getElementById("loginCode");

  function showMessage(text, type) {
    msg.textContent = text;
    msg.className = "form-message " + (type || "error");
    msg.style.display = "block";
  }

  // 1段階目：ID/パスワード送信
  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    msg.style.display = "none";
    ["err-id", "err-pw"].forEach(id => { document.getElementById(id).textContent = ""; });
    idEl.classList.remove("is-invalid");
    pwEl.classList.remove("is-invalid");

    let hasError = false;
    if (!idEl.value.trim()) {
      document.getElementById("err-id").textContent = "必須項目を入力してください";
      idEl.classList.add("is-invalid"); hasError = true;
    }
    if (!pwEl.value) {
      document.getElementById("err-pw").textContent = "必須項目を入力してください";
      pwEl.classList.add("is-invalid"); hasError = true;
    }
    if (hasError) return;

    btn.classList.add("is-loading");
    btn.disabled = true;
    try {
      const res = await fetch("/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ id: idEl.value.trim(), password: pwEl.value }),
      });
      const data = await res.json().catch(() => ({}));

      if (res.ok && data.status === "code_sent") {
        // メール確認コードの入力へ切り替え
        form.style.display = "none";
        verifyForm.style.display = "block";
        showMessage(data.message || "確認コードをメールに送信しました", "success");
        if (codeEl) codeEl.focus();
        return;
      }
      if (res.ok) {
        location.href = "/";
        return;
      }
      showMessage(data.message || "IDまたはパスワードが正しくありません", "error");
    } catch (err) {
      showMessage("サーバーに接続できませんでした。時間をおいて再度お試しください", "error");
    } finally {
      btn.classList.remove("is-loading");
      btn.disabled = false;
    }
  });

  // 2段階目：確認コード送信
  if (verifyForm) {
    verifyForm.addEventListener("submit", async (e) => {
      e.preventDefault();
      msg.style.display = "none";
      document.getElementById("err-code").textContent = "";

      if (!codeEl.value.trim()) {
        document.getElementById("err-code").textContent = "確認コードを入力してください";
        return;
      }

      verifyBtn.classList.add("is-loading");
      verifyBtn.disabled = true;
      try {
        const res = await fetch("/api/login-verify", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify({ code: codeEl.value.trim() }),
        });
        if (res.ok) {
          location.href = "/";
          return;
        }
        const data = await res.json().catch(() => ({}));
        showMessage(data.message || "確認コードが正しくありません", "error");
      } catch (err) {
        showMessage("サーバーに接続できませんでした。時間をおいて再度お試しください", "error");
      } finally {
        verifyBtn.classList.remove("is-loading");
        verifyBtn.disabled = false;
      }
    });
  }
}

// ===================== ダッシュボード画面 =====================
async function loadDashboard() {
  const list = document.getElementById("logList");
  const reply = document.getElementById("replyArea");
  if (!list || !reply) return;

  try {
    const res = await fetch("/api/dashboard");
    const rows = await res.json();

    if (!Array.isArray(rows) || rows.length === 0) {
      reply.innerHTML = '<p class="empty">まだ認識ログがありません</p>';
      list.innerHTML = '<div class="empty">履歴がまだありません</div>';
      return;
    }

    // 最新の1件を「最新のAI応答」に表示
    const latest = rows[0];
    reply.innerHTML =
      '<div class="meta-row">' +
        '<span>🕒 ' + esc(latest.timestamp) + '</span>' +
        '<span>❓ ' + esc(latest.query) + '</span>' +
        badge(latest.is_emergency) +
      '</div>' +
      '<p class="reply-text">' + esc(latest.response) + '</p>';

    // 全件をクリック可能なタイムラインで表示
    renderTimeline(list, rows);
  } catch (err) {
    reply.innerHTML = '<p class="empty">ログの取得に失敗しました</p>';
    list.innerHTML = '<div class="empty">ログの取得に失敗しました</div>';
  }
}

function initDashboard() {
  if (!document.getElementById("logList")) return;
  setupModalClose();
  loadDashboard();
  // 新しいログを受信したら自動反映（5秒ごと。モーダル表示中は更新しない）
  setInterval(() => { if (!isLogModalOpen()) loadDashboard(); }, 5000);
}

// ===================== 新規登録画面 =====================
function initRegister() {
  const form = document.getElementById("registerForm");
  if (!form) return;

  const msg = document.getElementById("formMessage");
  const btn = document.getElementById("registerBtn");
  const nameEl = document.getElementById("userName");
  const idEl = document.getElementById("loginId");
  const pwEl = document.getElementById("password");
  const pw2El = document.getElementById("password2");

  function showMessage(text, type) {
    msg.textContent = text;
    msg.className = "form-message " + (type || "error");
    msg.style.display = "block";
  }
  function setErr(id, text, el) {
    document.getElementById(id).textContent = text || "";
    if (el) el.classList.toggle("is-invalid", !!text);
  }

  form.addEventListener("submit", async (e) => {
    e.preventDefault();
    msg.style.display = "none";
    ["err-name", "err-id", "err-pw", "err-pw2"].forEach(id => setErr(id, ""));

    let hasError = false;
    if (!idEl.value.trim()) { setErr("err-id", "必須項目を入力してください", idEl); hasError = true; }
    if (pwEl.value.length < 8) { setErr("err-pw", "パスワードは8文字以上で入力してください", pwEl); hasError = true; }
    if (pw2El.value !== pwEl.value) { setErr("err-pw2", "パスワードが一致しません", pw2El); hasError = true; }
    if (hasError) return;

    btn.classList.add("is-loading");
    btn.disabled = true;
    try {
      const res = await fetch("/api/register", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          id: idEl.value.trim(),
          password: pwEl.value,
          name: nameEl.value.trim(),
        }),
      });
      const data = await res.json().catch(() => ({}));
      if (res.ok) {
        showMessage("登録が完了しました。ログイン画面へ移動します…", "success");
        setTimeout(() => { location.href = "/login"; }, 1500);
        return;
      }
      showMessage(data.message || "登録に失敗しました", "error");
    } catch (err) {
      showMessage("サーバーに接続できませんでした。時間をおいて再度お試しください", "error");
    } finally {
      btn.classList.remove("is-loading");
      btn.disabled = false;
    }
  });
}

// ===================== 履歴ログ画面 =====================
async function loadLogs() {
  const list = document.getElementById("fullLogList");
  if (!list) return;
  try {
    const res = await fetch("/api/dashboard");
    const rows = await res.json();
    renderTimeline(list, rows);
  } catch (err) {
    list.innerHTML = '<div class="empty">ログの取得に失敗しました</div>';
  }
}

function initLogs() {
  if (!document.getElementById("fullLogList")) return;
  setupModalClose();
  loadLogs();
  // 新しいログを受信したら自動反映（5秒ごと。モーダル表示中は更新しない）
  setInterval(() => { if (!isLogModalOpen()) loadLogs(); }, 5000);
}

function openLogDetail(row) {
  const modal = document.getElementById("logModal");
  if (!modal || !row) return;

  document.getElementById("md-query").textContent = row.query || "(質問なし)";
  document.getElementById("md-time").textContent = "🕒 " + (row.timestamp || "");
  document.getElementById("md-badge").innerHTML = badge(row.is_emergency);
  document.getElementById("md-response").textContent = row.response || "(回答なし)";

  const img = document.getElementById("md-image");
  const noimg = document.getElementById("md-noimage");
  if (row.image_url) {
    img.src = row.image_url;
    img.style.display = "block";
    noimg.style.display = "none";
  } else {
    img.style.display = "none";
    noimg.style.display = "block";
  }
  modal.style.display = "grid";
}

function closeLogDetail() {
  const modal = document.getElementById("logModal");
  if (modal) modal.style.display = "none";
}

// ===================== 通知・詳細設定画面 =====================
async function initSettings() {
  const saveBtn = document.getElementById("saveBtn");
  if (!saveBtn) return;

  const msg = document.getElementById("formMessage");
  const toggles = ["notify_conversation_log", "notify_periodic"];
  const texts = ["keyword", "user_name"];

  function showMessage(text, type) {
    msg.textContent = text;
    msg.className = "form-message " + (type || "error");
    msg.style.display = "block";
  }
  function isOn(v) { return v === "1" || v === 1 || v === true; }

  // 現在の設定を読み込んで反映
  try {
    const res = await fetch("/api/settings");
    const s = await res.json();
    toggles.forEach(k => { const el = document.getElementById(k); if (el) el.checked = isOn(s[k]); });
    texts.forEach(k => { const el = document.getElementById(k); if (el) el.value = s[k] || ""; });
  } catch (err) { /* 失敗時はデフォルト表示のまま */ }

  saveBtn.addEventListener("click", async () => {
    const payload = {};
    toggles.forEach(k => { const el = document.getElementById(k); payload[k] = el && el.checked ? "1" : "0"; });
    texts.forEach(k => { const el = document.getElementById(k); if (el) payload[k] = el.value.trim(); });

    saveBtn.classList.add("is-loading");
    saveBtn.disabled = true;
    msg.style.display = "none";
    try {
      const res = await fetch("/api/settings", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
      });
      const data = await res.json().catch(() => ({}));
      showMessage(res.ok ? "設定を保存しました" : (data.message || "保存に失敗しました"),
                  res.ok ? "success" : "error");
    } catch (err) {
      showMessage("サーバーに接続できませんでした", "error");
    } finally {
      saveBtn.classList.remove("is-loading");
      saveBtn.disabled = false;
    }
  });
}

// ===================== パスワード再設定（3ステップ） =====================
function initForgot() {
  const p1 = document.getElementById("forgotEmailForm");
  if (!p1) return;

  const p2 = document.getElementById("forgotCodeForm");
  const p3 = document.getElementById("forgotResetForm");
  const msg = document.getElementById("formMessage");
  let contact = "";

  function show(text, type) {
    msg.textContent = text;
    msg.className = "form-message " + (type || "error");
    msg.style.display = "block";
  }
  async function post(url, body) {
    const res = await fetch(url, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    });
    const data = await res.json().catch(() => ({}));
    return { ok: res.ok, data };
  }

  // ステップ1：メール入力 → コード送信
  p1.addEventListener("submit", async (e) => {
    e.preventDefault();
    msg.style.display = "none";
    const email = document.getElementById("fgEmail").value.trim();
    document.getElementById("err-fgEmail").textContent = "";
    if (!email) { document.getElementById("err-fgEmail").textContent = "メールアドレスを入力してください"; return; }
    try {
      const { ok, data } = await post("/api/send-auth-code", { contact: email });
      if (ok) {
        contact = email;
        p1.style.display = "none";
        p2.style.display = "block";
        show("確認コードをメールに送信しました", "success");
      } else {
        show(data.message || "送信に失敗しました", "error");
      }
    } catch (err) { show("サーバーに接続できませんでした", "error"); }
  });

  // ステップ2：コード検証
  p2.addEventListener("submit", async (e) => {
    e.preventDefault();
    msg.style.display = "none";
    const code = document.getElementById("fgCode").value.trim();
    document.getElementById("err-fgCode").textContent = "";
    if (!code) { document.getElementById("err-fgCode").textContent = "確認コードを入力してください"; return; }
    try {
      const { ok, data } = await post("/api/validate-auth-code", { contact, code });
      if (ok) {
        p2.style.display = "none";
        p3.style.display = "block";
        show("本人確認できました。新しいパスワードを設定してください", "success");
      } else {
        show(data.message || "確認コードが正しくないか、期限切れです", "error");
      }
    } catch (err) { show("サーバーに接続できませんでした", "error"); }
  });

  // ステップ3：新パスワード設定
  p3.addEventListener("submit", async (e) => {
    e.preventDefault();
    msg.style.display = "none";
    const pw = document.getElementById("fgPw").value;
    const pw2 = document.getElementById("fgPw2").value;
    document.getElementById("err-fgPw").textContent = "";
    document.getElementById("err-fgPw2").textContent = "";
    if (pw.length < 8) { document.getElementById("err-fgPw").textContent = "パスワードは8文字以上で入力してください"; return; }
    if (pw !== pw2) { document.getElementById("err-fgPw2").textContent = "パスワードが一致しません"; return; }
    try {
      const { ok, data } = await post("/api/reset-password", { id: contact, password: pw });
      if (ok) {
        show("パスワードを更新しました。ログイン画面へ移動します…", "success");
        setTimeout(() => { location.href = "/login"; }, 1500);
      } else {
        show(data.message || "更新に失敗しました", "error");
      }
    } catch (err) { show("サーバーに接続できませんでした", "error"); }
  });
}

document.addEventListener("DOMContentLoaded", () => {
  initLogin();
  initRegister();
  initForgot();
  initDashboard();
  initLogs();
  initSettings();
});
