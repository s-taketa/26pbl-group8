document.getElementById("register-form").addEventListener("submit", (e) => {
    e.preventDefault();
    const id = document.getElementById("reg-id");
    const pw = document.getElementById("reg-pw");
    const pwc = document.getElementById("reg-pw-confirm");
    
    // エラーメッセージとスタイルの初期化
    document.getElementById("reg-id-error").textContent = "";
    document.getElementById("reg-pw-error").textContent = "";
    document.getElementById("reg-pwc-error").textContent = "";
    id.classList.remove("is-invalid");
    pw.classList.remove("is-invalid");
    pwc.classList.remove("is-invalid");

    let valid = true;
    // 簡易的な形式チェック（@が含まれていない、かつ10文字未満ならエラー）
    if(!id.value.includes("@") && id.value.length < 10) {
        id.classList.add("is-invalid");
        document.getElementById("reg-id-error").textContent = "正しいメールアドレスまたは電話番号を入力してください";
        valid = false;
    }
    // パスワードの長さチェック
    if(pw.value.length < 8) {
        pw.classList.add("is-invalid");
        document.getElementById("reg-pw-error").textContent = "パスワードは8文字以上必要です";
        valid = false;
    }
    // パスワードの一致チェック
    if(pw.value !== pwc.value) {
        pwc.classList.add("is-invalid");
        document.getElementById("reg-pwc-error").textContent = "パスワードが一致しません";
        valid = false;
    }

    if(valid) {
        alert("登録申請を受け付けました。ログイン画面へ戻ります。");
        location.href = "login.html";
    }
});