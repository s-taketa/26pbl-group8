document.getElementById("reset-form").addEventListener("submit", (e) => {
    e.preventDefault(); // 画面のリロードを防ぐ

    const newPassword = document.getElementById("new-password");
    const confirmPassword = document.getElementById("confirm-password");
    const matchError = document.getElementById("match-error");

    // 一度エラー表示をクリアする
    matchError.textContent = "";
    newPassword.classList.remove("is-invalid");
    confirmPassword.classList.remove("is-invalid");

    // 1. 2つのパスワードが一致しているかチェック
    if (newPassword.value !== confirmPassword.value) {
        // ワイヤーフレーム通りのエラーメッセージを表示
        matchError.textContent = "二つのパスワードがあっていません";
        
        // 入力枠も少し赤くしてわかりやすくする
        newPassword.classList.add("is-invalid");
        confirmPassword.classList.add("is-invalid");
        return; // ここで処理をストップ
    }

    // 2. 空っぽじゃないかも念のためチェック
    if (!newPassword.value.trim() || !confirmPassword.value.trim()) {
        matchError.textContent = "パスワードを入力してください";
        return;
    }

    // パスワードが一致していた場合の処理
    alert("パスワードの再設定が完了しました。ログイン画面へ移動します。");
    window.location.href = "login.html";
});