# server/mailer.py
# 認証コードのメール送信（Gmail SMTP など）。標準ライブラリのみで実装。
# SMTP_USER / SMTP_PASS が未設定の場合は is_configured() が False を返し、
# 呼び出し側はログ出力にフォールバックする。

import os
import re
import ssl
import smtplib
from email.mime.text import MIMEText

SMTP_HOST = os.getenv("SMTP_HOST", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "465"))
SMTP_USER = os.getenv("SMTP_USER")           # 例: your_account@gmail.com
SMTP_PASS = os.getenv("SMTP_PASS")           # Gmailの「アプリパスワード」（通常のログインPWではない）
SMTP_FROM = os.getenv("SMTP_FROM", SMTP_USER)

_EMAIL_RE = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


def is_email(addr: str) -> bool:
    """メールアドレス形式かどうかの簡易判定"""
    return bool(addr and _EMAIL_RE.match(addr))


def is_configured() -> bool:
    """SMTP送信に必要な情報が揃っているか"""
    return bool(SMTP_USER and SMTP_PASS)


def send_email_code(to_addr: str, code: str) -> None:
    """認証コードをメールで送信する。失敗時は例外を送出する。"""
    if not is_configured():
        raise RuntimeError("SMTP未設定（SMTP_USER / SMTP_PASS を設定してください）")

    body = (
        "コエミマ 見守りアシスタントの認証コードをお知らせします。\n\n"
        f"    認証コード： {code}\n\n"
        "5分以内に画面へ入力してください。\n"
        "※このメールに心当たりがない場合は破棄してください。"
    )
    msg = MIMEText(body, "plain", "utf-8")
    msg["Subject"] = "【コエミマ】パスワード再設定の認証コード"
    msg["From"] = SMTP_FROM
    msg["To"] = to_addr

    context = ssl.create_default_context()
    if SMTP_PORT == 465:
        # SSL（Gmailの推奨ポート）
        with smtplib.SMTP_SSL(SMTP_HOST, SMTP_PORT, context=context, timeout=15) as server:
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)
    else:
        # STARTTLS（587番など）
        with smtplib.SMTP(SMTP_HOST, SMTP_PORT, timeout=15) as server:
            server.ehlo()
            server.starttls(context=context)
            server.login(SMTP_USER, SMTP_PASS)
            server.send_message(msg)