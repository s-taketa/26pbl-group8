document.getElementById("reset-form").addEventListener("submit", (e) => {
    e.preventDefault(); // フォーム送信による画面リロードを防ぐ

    const newPassword = document.getElementById("new-password");
    const confirmPassword = document.getElementById("confirm-password");
    const matchError = document.getElementById("match-error");

    // 状態を一度クリアする
    matchError.textContent = "";
    newPassword.classList.remove("is-invalid");
    confirmPassword.classList.remove("is-invalid");

    // 1. 2つのパスワードが一致しているかチェック
    if (newPassword.value !== confirmPassword.value) {
        // ワイヤーフレーム通りのエラー文言をセット
        matchError.textContent = "二つのパスワードがあっていません";
        
        // 入力フォームの枠線も赤くする（style.cssのis-invalidクラスを適用）
        newPassword.classList.add("is-invalid");
        confirmPassword.classList.add("is-invalid");
        return; // ここで処理を中断
    }

    // 2. 空白チェック（念のため）
    if (!newPassword.value.trim() || !confirmPassword.value.trim()) {
        matchError.textContent = "パスワードを入力してください";
        return;
    }

    // パスワードが完全に一致していた場合
    alert("パスワードの再設定が完了しました。ログイン画面へ移動します。");
    window.location.href = "login.html";
});