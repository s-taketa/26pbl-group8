// =============================================
// 設定: バックエンドのエンドポイントが決まったらここを変更するだけでOK
// =============================================
const API_BASE_URL = "/api";
const VERIFY_CODE_ENDPOINT = `${API_BASE_URL}/auth/verify-code`;

const form = document.getElementById("verify-form");
const digitInputs = Array.from(document.querySelectorAll(".code-digit"));
const submitBtn = document.getElementById("submit-btn");
const formMessage = document.getElementById("form-message");
const codeError = document.getElementById("code-error");

// -------------------------------------------
// 1マスずつの入力UX（自動フォーカス移動）
// -------------------------------------------

digitInputs.forEach((input, index) => {
    // 数字以外を即時除去
    input.addEventListener("input", () => {
        input.value = input.value.replace(/[^0-9]/g, "");
        clearFieldError();

        if (input.value && index < digitInputs.length - 1) {
            digitInputs[index + 1].focus();
        }
    });

    // Backspaceで空欄なら前のマスへ戻る
    input.addEventListener("keydown", (e) => {
        if (e.key === "Backspace" && !input.value && index > 0) {
            digitInputs[index - 1].focus();
        }
    });

    // ペースト操作で4桁まとめて入力できるように
    input.addEventListener("paste", (e) => {
        e.preventDefault();
        const pasted = (e.clipboardData || window.clipboardData)
            .getData("text")
            .replace(/[^0-9]/g, "")
            .slice(0, digitInputs.length);

        pasted.split("").forEach((char, i) => {
            if (digitInputs[i]) digitInputs[i].value = char;
        });

        const nextEmptyIndex = pasted.length < digitInputs.length ? pasted.length : digitInputs.length - 1;
        digitInputs[nextEmptyIndex].focus();
        clearFieldError();
    });
});

function getCode() {
    return digitInputs.map((input) => input.value).join("");
}

function clearFieldError() {
    digitInputs.forEach((input) => input.classList.remove("is-invalid"));
    codeError.hidden = true;
    codeError.textContent = "";
}

function showFieldError(message) {
    digitInputs.forEach((input) => input.classList.add("is-invalid"));
    codeError.textContent = message;
    codeError.hidden = false;
}

// -------------------------------------------
// UI 表示ヘルパー
// -------------------------------------------

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

async function verifyCodeApi(code) {
    // ===== 本番実装イメージ（仕様確定後に差し替え） =====
    // const res = await fetch(VERIFY_CODE_ENDPOINT, {
    //     method: "POST",
    //     headers: { "Content-Type": "application/json" },
    //     body: JSON.stringify({ code }),
    // });
    // if (!res.ok) {
    //     const data = await res.json().catch(() => ({}));
    //     throw new Error(data.message || "認証コードが正しくありません");
    // }
    // return res.json(); // 例: { ok: true, reset_token: "..." }

    // ===== 現在はモック実装 =====
    console.log("[MOCK] 認証コード送信:", { code });
    await new Promise((resolve) => setTimeout(resolve, 600));

    if (code === "0000") {
        throw new Error("認証コードが正しくありません");
    }
    return { ok: true };
}

// -------------------------------------------
// フォーム送信処理
// -------------------------------------------

form.addEventListener("submit", async (e) => {
    e.preventDefault();
    clearFormMessage();
    clearFieldError();

    const code = getCode();

    if (code.length !== digitInputs.length) {
        showFieldError("4桁すべて入力してください");
        digitInputs.find((input) => !input.value)?.focus();
        return;
    }

    setLoading(true);
    try {
        await verifyCodeApi(code);
        showFormMessage("認証に成功しました。画面を移動します…", "success");
        // TODO: バックエンド確定後、新しいパスワード設定画面への遷移を実装
        // 例: window.location.href = `reset-password.html?token=${result.reset_token}`;
    } catch (err) {
        showFieldError(err.message || "認証コードが正しくありません");
        digitInputs.forEach((input) => (input.value = ""));
        digitInputs[0].focus();
    } finally {
        setLoading(false);
    }
});
