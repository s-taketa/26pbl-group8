// =============================================
// 設定: バックエンドのエンドポイントが決まったらここを変更するだけでOK
// =============================================
const API_BASE_URL = "/api";
const FORGOT_PASSWORD_ENDPOINT = `${API_BASE_URL}/auth/forgot-password`;

const form = document.getElementById("forgot-form");
const loginIdInput = document.getElementById("login-id");
const submitBtn = document.getElementById("submit-btn");
const formMessage = document.getElementById("form-message");
const loginIdError = document.getElementById("login-id-error");

// -------------------------------------------
// バリデーション（login.js / register.js と基準を統一）
// -------------------------------------------

function isEmail(value) {
    return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value);
}

function isPhoneNumber(value) {
    return /^0\d{1,4}-?\d{1,4}-?\d{3,4}$/.test(value.replace(/\s/g, ""));
}

function validateLoginId(value) {
    if (!value) return "メールアドレスまたは電話番号を入力してください";
    if (!isEmail(value) && !isPhoneNumber(value)) {
        return "メールアドレスまたは電話番号の形式が正しくありません";
    }
    return null;
}

// -------------------------------------------
// UI 表示ヘルパー
// -------------------------------------------

function showFieldError(inputEl, errorEl, message) {
    if (message) {
        inputEl.classList.add("is-invalid");
        inputEl.setAttribute("aria-invalid", "true");
        errorEl.textContent = message;
        errorEl.hidden = false;
    } else {
        inputEl.classList.remove("is-invalid");
        inputEl.removeAttribute("aria-invalid");
        errorEl.hidden = true;
        errorEl.textContent = "";
    }
}

function showFormMessage(message, type = "error") {
    formMessage.textContent = message;
    formMessage.className = `form-message ${type}`;
    formMessage.hidden = false;
}

function clearFormMessage() {
    formMessage.hidden = true;
    formMessage.textContent = "";
}

function setLoading(isLoading) {
    submitBtn.disabled = isLoading;
    submitBtn.classList.toggle("is-loading", isLoading);
}

// -------------------------------------------
// API呼び出し（現時点ではモック。仕様確定後にここだけ差し替える）
// -------------------------------------------

async function forgotPasswordApi(loginId) {
    // ===== 本番実装イメージ（仕様確定後に差し替え） =====
    // const res = await fetch(FORGOT_PASSWORD_ENDPOINT, {
    //     method: "POST",
    //     headers: { "Content-Type": "application/json" },
    //     body: JSON.stringify({ login_id: loginId }),
    // });
    // if (!res.ok) {
    //     const data = await res.json().catch(() => ({}));
    //     throw new Error(data.message || "送信に失敗しました");
    // }
    // return res.json(); // 例: { ok: true }

    // ===== 現在はモック実装 =====
    console.log("[MOCK] パスワードリセット送信:", { loginId });
    await new Promise((resolve) => setTimeout(resolve, 600));

    if (loginId === "notfound@example.com") {
        throw new Error("登録されていないメールアドレス・電話番号です");
    }
    return { ok: true };
}

// -------------------------------------------
// フォーム送信処理
// -------------------------------------------

form.addEventListener("submit", async (e) => {
    e.preventDefault();
    clearFormMessage();

    const loginId = loginIdInput.value.trim();
    const loginIdErr = validateLoginId(loginId);

    showFieldError(loginIdInput, loginIdError, loginIdErr);

    if (loginIdErr) {
        loginIdInput.focus();
        return;
    }

    setLoading(true);
    try {
        await forgotPasswordApi(loginId);
        // TODO: バックエンド確定後、次の画面（コード入力 or 完了画面）への遷移を実装
        showFormMessage("再設定用の案内を送信しました。メール・SMSをご確認ください。", "success");
    } catch (err) {
        showFormMessage(err.message || "送信に失敗しました。時間をおいて再度お試しください。", "error");
    } finally {
        setLoading(false);
    }
});

// 入力中にエラー表示をリアルタイムで解除
loginIdInput.addEventListener("input", () => {
    if (loginIdInput.classList.contains("is-invalid")) {
        showFieldError(loginIdInput, loginIdError, null);
    }
});
