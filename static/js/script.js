const form = document.getElementById('loginForm');
const usernameInput = document.getElementById('username');
const passwordInput = document.getElementById('password');
const errorMsg = document.getElementById('error-message');

form.addEventListener('submit', function(e) {
    e.preventDefault(); // 画面の勝手なリロードを完全にストップ

    // 【テスト用の判定ロジック】
    // パスワード欄に「error」と入力してボタンを押すと、赤文字でエラーが出ます。
    // それ以外のパスワードを入力すれば、確実にメイン画面（dashboard.html）に飛びます。
    if (passwordInput.value === "error") {
        errorMsg.style.display = 'block';
        passwordInput.style.borderColor = '#ff0000';
        usernameInput.style.borderColor = '#ff0000';
    } else {
        errorMsg.style.display = 'none';
        passwordInput.style.borderColor = '#cccccc';
        usernameInput.style.borderColor = '#cccccc';

        alert("ログインに成功しました！メイン画面（dashboard.html）へ移動します。");
        
        // 🟢 ここでメイン画面（dashboard.html）へ確実にジャンプします
        window.location.href = 'dashboard.html'; 
    }
});

// ユーザーが文字を打ち直し始めたらエラーの赤文字を消す親切設計
usernameInput.addEventListener('input', () => {
    errorMsg.style.display = 'none';
    usernameInput.style.borderColor = '#cccccc';
    passwordInput.style.borderColor = '#cccccc';
});
passwordInput.addEventListener('input', () => {
    errorMsg.style.display = 'none';
    usernameInput.style.borderColor = '#cccccc';
    passwordInput.style.borderColor = '#cccccc';
});