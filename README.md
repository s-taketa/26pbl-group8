# 26pbl-group8 - AI見守りアシスタント

## 📋 目次

- [概要](#概要)
- [リポジトリ構成](#リポジトリ構成)
- [システムアーキテクチャ](#システムアーキテクチャ)
- [Docker 構成](#docker-構成)
- [環境変数設定](#環境変数設定)
- [セットアップ手順](#セットアップ手順)
- [使用例](#使用例)
- [トラブルシューティング](#トラブルシューティング)
- [停止とクリーンアップ](#停止とクリーンアップ)
- [主要な技術スタック](#主要な技術スタック)
- [開発フロー](#開発フロー)

---

## 概要

本プロジェクトは、Raspberry Pi 5（エッジ側）とUbuntuサーバー（管理側）で構成される**次世代AI見守りアシスタント**です。カメラ映像の解析、音声認識、AI判断、そして家族への自動通知機能を備えています。

### 主要機能

- 🎥 リアルタイム映像解析（OpenCV + Google Gemini API）
- 🎤 音声認識・合成（Vosk / Whisper + VOICEVOX）
- 💭 AI会話エンジン（Google Gemini API 1.5 Flash）
- 📱 LINE Messaging API による家族通知
- 📊 ログ管理・UI ダッシュボード
- 🔐 ユーザー認証（電話番号/メールアドレス）

---

## リポジトリ構成

```
26pbl-group8/                           # リポジトリルート
├── .env                                # 機密情報管理 (Gemini API, LINEトークン, DB情報)
├── .gitignore                          # Git管理除外設定
├── docker-compose.yml                  # コンテナ管理 (app, db, voicevox)
├── Dockerfile                          # Python 3.11-slimベースの実行環境定義
├── requirements.txt                    # Pythonライブラリ一覧 (Gemini, OpenCV, Vosk等)
├── README.md                           # このファイル
│
├── edge/                               # エッジ側アプリケーション (Raspberry Pi 5用)
│   ├── app.py                          # サーバー命令待ち受け用Flaskサーバー
│   ├── ai_logic.py                     # Gemini API (1.5 Flash) による状況判断ロジック
│   ├── image_processor.py              # カメラキャプチャ・RGB入れ替え処理
│   ├── keyword_listener.py             # Voskによる「起動して」等の常時監視
│   └── voice_handler.py                # Whisper(STT)およびVOICEVOX(TTS)制御
│
├── server/                             # サーバー側アプリケーション (Ubuntuサーバー用)
│   ├── main.py                         # 管理画面・API制御のメインプログラム
│   ├── database.py                     # SQLAlchemyによるMySQL接続・DB操作
│   ├── models.py                       # MySQLテーブル定義 (users, logs等)
│   ├── line_notifier.py                # LINE Messaging APIによる家族通知
│   │
│   ├── static/                         # フロントエンド静的ファイル
│   │   ├── css/
│   │   │   └── style.css               # ユニバーサルデザイン用スタイルシート
│   │   └── js/
│   │       └── main.js                 # リアルタイム更新・通信制御
│   │
│   └── templates/                      # HTMLテンプレートファイル
│       ├── index.html                  # ダッシュボード (映像、ログ、通知表示)
│       └── login.html                  # 認証画面 (電話番号/メールアドレス)
│
└── sql/                                # データベース関連
    └── schema.sql                      # MySQL初期化スクリプト
```

---

## システムアーキテクチャ

```
┌─────────────────────────────────────────────────────┐
│           Raspberry Pi 5（エッジ側）                  │
├──────────────────────┬──────────────────────────────┤
│ カメラ / USB マイク   │  Docker コンテナ群           │
│  (/dev/video0)       │  ┌──────────────────────┐   │
│                      │  │  Flask/FastAPI App   │   │
│                      │  │  (Python 3.11)       │   │
│                      │  ├──────────────────────┤   │
│                      │  │  OpenCV 映像処理     │   │
│                      │  │  Google Gemini API   │   │
│                      │  └──────────────────────┘   │
└──────────────────────┴──────────────────────────────┘
           ↓ ネットワーク接続 ↓
┌─────────────────────────────────────────────────────┐
│        Ubuntu サーバー（管理側）                      │
├──────────────────────┬──────────────────────────────┤
│ Docker コンテナ群    │                              │
│ ┌────────────────┐  │                              │
│ │ MySQL Database │  │  中央ログ・ユーザー管理      │
│ │ (MySQL 8.0)    │  │  映像・ログデータ永続化      │
│ └────────────────┘  │                              │
│ ┌────────────────┐  │                              │
│ │ VOICEVOX       │  │  音声合成エンジン            │
│ │ (API サーバー) │  │  (Linux ARM64版)            │
│ └────────────────┘  │                              │
└──────────────────────┴──────────────────────────────┘
```

---

## Docker 構成

### サービス一覧

| サービス | 用途 | ポート | 依存関係 |
|---------|------|--------|--------|
| **app** | Flask/FastAPI メインアプリケーション | 5000, 8000 | db, voicevox |
| **db** | MySQL データベース | 3306 | - |
| **voicevox** | 音声合成エンジン | 50021 | - |

### ボリューム（永続化ストレージ）

| ボリューム名 | マウント先 | 用途 |
|-------------|----------|------|
| `app-logs` | `/app/logs` | アプリケーションログ |
| `image-storage` | `/app/images` | 認識画像、スクリーンショット |
| `voicevox-audio` | `/app/audio` | 合成音声ファイル |
| `mysql-data` | `/var/lib/mysql` | MySQL データベースファイル |

### ネットワーク

- **ネットワーク名**: `ai-assistant-network`
- **ドライバー**: bridge
- **用途**: コンテナ間通信。アプリから `db`、`voicevox` という名前で各サービスに接続可能

### ハードウェアアクセス設定

app コンテナは以下のデバイスにアクセスします（Raspberry Pi 環境）:

- `/dev/video0`: カメラモジュール
- USB マイク・その他 I/O デバイス

```yaml
privileged: true  # ハードウェアアクセス権限を付与
devices:
  - /dev/video0:/dev/video0  # カメラ
```

---

## 環境変数設定

### 方法 1: `.env` ファイルを使用（推奨）

リポジトリルートに `.env` ファイルを作成:

```bash
# Google Gemini API キー
GOOGLE_GEMINI_API_KEY=your-api-key-here

# MySQL 設定
MYSQL_ROOT_PASSWORD=rootpassword
DB_USER=ai_assistant
DB_PASSWORD=changeme
DB_NAME=ai_assistant_db

# Flask 環境
FLASK_ENV=production
```

`docker-compose.yml` が自動的に `.env` ファイルを読み込みます。

### 方法 2: コマンドラインで指定

```bash
docker-compose up -e GOOGLE_GEMINI_API_KEY=your-key
```

### 環境変数一覧

| 変数名 | 説明 | デフォルト |
|--------|------|----------|
| `GOOGLE_GEMINI_API_KEY` | Google Gemini API キー | 未設定 |
| `DB_HOST` | MySQL ホスト（docker-compose 内では `db`） | `db` |
| `DB_PORT` | MySQL ポート | `3306` |
| `DB_USER` | MySQL ユーザー名 | `ai_assistant` |
| `DB_PASSWORD` | MySQL パスワード | `changeme` |
| `DB_NAME` | MySQL データベース名 | `ai_assistant_db` |
| `VOICEVOX_HOST` | VOICEVOX ホスト | `voicevox` |
| `VOICEVOX_PORT` | VOICEVOX ポート | `50021` |
| `FLASK_ENV` | Flask 環境（development/production） | `production` |

---

## セットアップ手順

### 前提条件

- **Docker**: 20.10 以上
- **Docker Compose**: 1.29 以上
- **Raspberry Pi 5**: arm64 アーキテクチャ対応
- **Python**: 3.11 以上（ホスト側：オプション）

### 1. リポジトリのクローン

```bash
git clone https://github.com/s-taketa/26pbl-group8.git
cd 26pbl-group8
```

### 2. 環境ファイルの作成

```bash
# .env ファイルを作成（テンプレートを参照）
cp .env.example .env

# または手動で .env を作成
cat > .env << EOF
GOOGLE_GEMINI_API_KEY=your-api-key-here
DB_USER=ai_assistant
DB_PASSWORD=changeme
MYSQL_ROOT_PASSWORD=rootpassword
FLASK_ENV=production
EOF
```

### 3. Docker イメージのビルド

```bash
docker-compose build
```

### 4. サービスの起動

```bash
# バックグラウンドで起動
docker-compose up -d

# フォアグラウンド（ログ表示）で起動
docker-compose up
```

### 5. サービスの確認

```bash
# 実行中のコンテナ確認
docker-compose ps

# ログ確認
docker-compose logs app       # app コンテナのログ
docker-compose logs db        # db コンテナのログ
docker-compose logs voicevox  # VOICEVOX のログ

# リアルタイムログ監視
docker-compose logs -f app
```

---

## 使用例

### Flask / FastAPI へのアクセス

```bash
# Flask アプリケーション
curl http://localhost:5000/health

# FastAPI アプリケーション（使用している場合）
curl http://localhost:8000/docs
```

### VOICEVOX API へのアクセス

```bash
# 音声合成リクエスト例
curl -X POST "http://localhost:50021/synthesis" \
  -H "Content-Type: application/json" \
  -d '{"text": "こんにちは", "speaker": 1}'
```

### MySQL へのアクセス

```bash
# ホストから MySQL コンテナに接続
mysql -h 127.0.0.1 -u ai_assistant -p ai_assistant_db

# コンテナ内から接続
docker-compose exec db mysql -u ai_assistant -p ai_assistant_db
```

---

## トラブルシューティング

### コンテナが起動しない

```bash
# ログで詳細を確認
docker-compose logs app

# コンテナの詳細情報を確認
docker inspect <container_id>
```

### MySQL に接続できない

```bash
# MySQL が正常に起動しているか確認
docker-compose ps db

# MySQL ヘ���スチェックを実行
docker-compose exec db mysqladmin ping -h localhost
```

### カメラデバイスが見つからない

Raspberry Pi 環境を確認:

```bash
# ホスト側でカメラが認識されているか確認
ls -la /dev/video*

# コンテナ内からアクセス確認
docker-compose exec app ls -la /dev/video0
```

### メモリ不足（Raspberry Pi の場合）

`docker-compose.yml` でメモリ制限を調整:

```yaml
services:
  voicevox:
    deploy:
      resources:
        limits:
          memory: 512M  # 512MB に調整
```

---

## 停止とクリーンアップ

### サービスの停止

```bash
# 実行中のコンテナを停止
docker-compose down

# データを保持して停止
docker-compose stop

# データもすべて削除
docker-compose down -v
```

---

## 主要な技術スタック

| コンポーネント | 用途 |
|--------------|------|
| **Python 3.11** | 開発言語 |
| **Flask / FastAPI** | Web フレームワーク |
| **OpenCV** | 映像処理・顔認識 |
| **Google Gemini API** | AI 対話エンジン |
| **VOICEVOX** | 音声合成 |
| **MySQL 8.0** | データベース |
| **Vosk / SpeechRecognition** | 音声認識 |
| **LINE Messaging API** | 家族通知 |

---

## 開発フロー

### Branch Protection Rules (main)

mainブランチは以下のルールで保護されています。

#### ■ Rules

- Require a pull request before merging
- Require approvals
  - Required approvals: 1
- Require approval of the most recent reviewable push
- Dismiss stale pull request approvals when new commits are pushed
- Require conversation resolution before merging
- Do not allow bypassing the above settings

#### ■ Development Flow

このリポジトリでは以下のフローで開発を行います。

1. featureブランチを作成する  
   例：`feature/login-function`
2. 作業後、Pull Requestを作成する（mainへ直接pushは禁止）
3. 他メンバーがレビュー（1人以上）
4. 修正があれば対応
5. 承認後、mainへマージ

#### ■ Notes

- mainブランチへの直接pushは禁止
- 必ずPull Requestを経由すること
- レビュー後に変更を加えた場合は、再レビューが必要
