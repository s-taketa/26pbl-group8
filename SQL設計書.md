
---

### データベース設計書 (SQLite)

#### 1. 概要
本システムでは、Raspberry Pi 5上での動作を考慮し、軽量でサーバーレスな **SQLite** を採用します。
要介護者のプライバシーを守りつつ、家族（補助者）が後から状況を確認できるよう、認識ログ、通知、設定情報を管理します。

#### 2. テーブル定義
プロジェクトの命名規則に基づき、テーブル名は `snake_case`、カラム名は `camelCase` で統一します。

##### 2.1 `users` (ユーザー管理)
画面設計案にあるログイン機能（電話番号/メールアドレス、パスワード）を支えるテーブルです。

| カラム名 | 型 | 制約 | 説明 |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | ユーザーID |
| `emailOrPhone` | TEXT | UNIQUE, NOT NULL | ログイン用ID（メールまたは電話番号） |
| `passwordHash` | TEXT | NOT NULL | ハッシュ化されたパスワード |
| `userName` | TEXT | | 表示名（「名前の設定」画面で変更可能） |
| `createdAt` | DATETIME | DEFAULT CURRENT_TIMESTAMP | 登録日時 |

##### 2.2 `recognitionLogs` (認識・対話ログ)
要介護者の発言、AIの回答、その際の画像を保存します。画面上の「log」セクションに表示されます。

| カラム名 | 型 | 制約 | 説明 |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | ログID |
| `timestamp` | DATETIME | DEFAULT CURRENT_TIMESTAMP | 発生日時 |
| `imagePath` | TEXT | | 保存画像のパス（「リアルタイム画像or認識した画像」） |
| `userQuery` | TEXT | | 要介護者が聞いた内容（音声認識結果） |
| `aiResponse` | TEXT | | AI（Gemini）が生成した回答内容 |
| `isEmergency` | INTEGER | DEFAULT 0 | 緊急性の有無（1:緊急, 0:通常） |

##### 2.3 `notificationHistory` (通知・行動履歴)
家族へのLINE通知や、画面上の「行動の履歴」を表示するためのテーブルです。

| カラム名 | 型 | 制約 | 説明 |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | 通知ID |
| `timestamp` | DATETIME | DEFAULT CURRENT_TIMESTAMP | 通知日時 |
| `category` | TEXT | | 通知の種類（薬の飲み忘れ、転倒の予兆、生存確認等） |
| `message` | TEXT | | 通知メッセージの内容 |
| `isRead` | INTEGER | DEFAULT 0 | 既読フラグ（1:既読, 0:未読） |

##### 2.4 `systemSettings` (システム設定)
「通知設定」や「名前の設定」など、画面設計案の右側にある設定項目を保持します。

| カラム名 | 型 | 制約 | 説明 |
| :--- | :--- | :--- | :--- |
| `settingKey` | TEXT | PRIMARY KEY | 設定項目名（`notification_enabled`, `gemini_api_key`等） |
| `settingValue` | TEXT | | 設定値 |
| `category` | TEXT | | 設定の分類（`alert`, `general`, `api`） |
| `updatedAt` | DATETIME | | 最終更新日時 |

---