# コエミマ — AI見守りアシスタント

Raspberry Pi 5（エッジ）と Ubuntu サーバー（管理・処理集約）で構成する、声で使える見守りシステム。話しかけると AI がカメラ映像を解析して状況を音声で答え、危険を検知すると家族へ LINE 通知する。

## 主要機能
- 🎤 オフライン音声認識（Vosk）＋物理ボタン起動
- 🤖 マルチモーダルAI解析（Google Gemini 2.5 Flash）
- 🔊 音声合成（VOICEVOX・文単位ストリーミング）
- 🚨 緊急検知 → LINE Messaging API 通知
- 📊 家族向けダッシュボード（映像・履歴・設定）
- 🔐 認証（ハッシュ・メール2段階・パスワード再設定）

## リポジトリ構成
```
26pbl-group8/
├── docker-compose.yml        # app / db / voicevox
├── Dockerfile
├── requirements.txt
├── .env                      # 機密情報（Git管理外にすること）
├── edge/                     # Raspberry Pi 5（Pi上で直接実行）
│   ├── app.py                # Flask(/video,/command)・認識フロー・再生・ボタン
│   ├── keyword_listener.py   # Vosk STT（ウェイクワード＋コマンド）
│   └── image_processor.py    # Picamera2 撮影・NoIR補正
├── server/                   # Ubuntu（Docker）
│   ├── main.py               # Flask アプリ本体（API・画面・通知）
│   ├── main_controller.py    # 認証・登録・設定・ダッシュボード
│   ├── ai_logic.py           # Gemini 解析
│   ├── voice_handler.py      # VOICEVOX 音声合成（ストリーム）
│   ├── database.py / models.py  # MySQL / SQLAlchemy
│   ├── line_notifier.py      # LINE 通知
│   ├── mailer.py             # Gmail SMTP（認証コード）
│   ├── templates/            # login/register/forgot/index/logs/settings
│   └── static/               # css / js
└── sql/schema.sql
```

## セットアップ（要点）
詳細は「開発/環境構築・デプロイ手順書.md」。
```bash
# サーバー
cd ~/26pbl-group8
docker compose up -d --build
docker compose logs -f app        # Running on 0.0.0.0:5000
# ブラウザ http://<サーバーIP>:5000/login → 新規登録
```
```bash
# エッジ（Pi）
cd /home/pbl8/edge && bash start.sh
```

## 技術スタック
Python 3.11 / Flask / Google Gemini API(2.5 Flash) / VOICEVOX / MySQL 8.0 / SQLAlchemy+PyMySQL / Vosk / OpenCV・Picamera2 / gpiozero / LINE Messaging API / Gmail SMTP / Docker Compose

## 開発フロー
- `main`：本番（直接push禁止・PR必須・1名以上レビュー）
- `develop`：開発統合
- `feature/xxx`：機能単位

> ⚠️ Gemini/LINE/SMTP の鍵は `.env` に置き、Git にコミットしないこと。`.env.example` はダミー値のみ。
