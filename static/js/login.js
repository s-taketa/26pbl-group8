document.getElementById("login-form").addEventListener("submit", async (e) => {
    e.preventDefault();
    const idInput = document.getElementById("login-id");
    const pwInput = document.getElementById("password");
    const idError = document.getElementById("id-error");
    const pwError = document.getElementById("pw-error");
    const mainError = document.getElementById("main-error");
    const btn = document.getElementById("next-btn");

    // エラー表示の初期化
    idInput.classList.remove("is-invalid");
    pwInput.classList.remove("is-invalid");
    idError.textContent = "";
    pwError.textContent = "";
    mainError.textContent = "";

    let isValid = true;
    if (!idInput.value.trim()) {
        idInput.classList.add("is-invalid");
        idError.textContent = "IDを入力してください";
        isValid = false;
    }
    if (!pwInput.value.trim()) {
        pwInput.classList.add("is-invalid");
        pwError.textContent = "パスワードを入力してください";
        isValid = false;
    }
    if (!isValid) return;

    btn.disabled = true;
    btn.textContent = "ログイン中...";

    // 模擬API通信（1秒後に処理完了）
    setTimeout(() => {
        console.log("ログイン送信（IDのみログ出力）:", idInput.value);
        alert("ログイン成功（仮） ダッシュボードへ進みます");
        btn.disabled = false;
        btn.textContent = "次へ";
    }, 1000);
});