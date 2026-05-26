
---

### データベース設計書 (MySQL 専有版)

#### 1. 概要
本システムは、すべてのデータを Ubuntu サーバー上の **MySQL** で一括管理します。エッジデバイス（Raspberry Pi 5）で発生した認識イベントやログは、リアルタイムでこの中央DBに保存されます。

#### 2. テーブル定義
プロジェクト規約に基づき、テーブル名・カラム名はすべて **snake_case** とします。

##### 2.1 `users` (ユーザー管理)
補助者のログイン情報およびプロフィールを管理します。

| カラム名 | 型 | 制約 | 説明 |
| :--- | :--- | :--- | :--- |
| `id` | INT | PRIMARY KEY AUTO_INCREMENT | ユーザーID |
| `login_id` | VARCHAR(255) | UNIQUE, NOT NULL | 電話番号またはメールアドレス |
| `password_hash` | VARCHAR(255) | NOT NULL | ハッシュ化されたパスワード |
| `user_name` | VARCHAR(100) | | 表示名（「名前の設定」用） |
| `created_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | 登録日時 |

##### 2.2 `recognition_logs` (認識・対話ログ)
Gemini APIによる解析結果の全履歴です。画面の「log」セクションに表示されます。

| カラム名 | 型 | 制約 | 説明 |
| :--- | :--- | :--- | :--- |
| `id` | INT | PRIMARY KEY AUTO_INCREMENT | ログID |
| `timestamp` | DATETIME | DEFAULT CURRENT_TIMESTAMP | 発生日時 |
| `image_path` | VARCHAR(500) | | サーバー上の画像保存先パス |
| `user_query` | TEXT | | 音声認識された質問内容 |
| `ai_response` | TEXT | | AIが生成した回答内容 |
| `is_emergency` | TINYINT(1) | DEFAULT 0 | 緊急判定（1:緊急, 0:通常） |

##### 2.3 `notification_history` (通知・行動履歴)
家族へのLINE通知内容や、画面上の「行動の履歴」を表示するためのデータです。

| カラム名 | 型 | 制約 | 説明 |
| :--- | :--- | :--- | :--- |
| `id` | INT | PRIMARY KEY AUTO_INCREMENT | 通知ID |
| `timestamp` | DATETIME | DEFAULT CURRENT_TIMESTAMP | 通知日時 |
| `category` | VARCHAR(50) | | 通知種別（薬、転倒予兆、生存確認等） |
| `message` | TEXT | | 通知メッセージの内容 |
| `is_read` | TINYINT(1) | DEFAULT 0 | 既読フラグ（1:既読, 0:未読） |

##### 2.4 `system_settings` (システム設定)
「通知設定」や「キーワード設定」など、画面から変更可能な各種パラメータです。

| カラム名 | 型 | 制約 | 説明 |
| :--- | :--- | :--- | :--- |
| `setting_key` | VARCHAR(100) | PRIMARY KEY | 設定キー名 |
| `setting_value` | TEXT | | 設定値 |
| `category` | VARCHAR(50) | | 設定分類（alert, user, api等） |
| `updated_at` | DATETIME | ON UPDATE CURRENT_TIMESTAMP | 最終更新日時 |

---

### MySQL化による変更点
*   **型定義の最適化**: SQLiteの `INTEGER` から MySQLの `INT` や `TINYINT(1)`、`VARCHAR` へ、より厳密な型定義に変更しました。
*   **自動採番**: `AUTOINCREMENT` (SQLite) を `AUTO_INCREMENT` (MySQL) に修正しました。
*   **運用の簡略化**: ラズパイ側でSQLiteの同期処理を書く必要がなくなり、すべての `feature` ブランチにおいて「MySQLへの接続」を前提とした実装が可能になります。

これでDB周りは完璧にMySQL仕様になりました。

この新しい設計書を基に、**GitHubの Pull Request を更新**してしまいましょうか？それとも、MySQLに接続するための **Python (SQLAlchemyなど) のベースコード**を作成しましょうか？
---

### データベース設計書 (MySQL 専有版)

#### 1. 概要
本システムは、すべてのデータを Ubuntu サーバー上の **MySQL** で一括管理します。エッジデバイス（Raspberry Pi 5）で発生した認識イベントやログは、リアルタイムでこの中央DBに保存されます。

#### 2. テーブル定義
プロジェクト規約に基づき、テーブル名・カラム名はすべて **snake_case** とします。

##### 2.1 `users` (ユーザー管理)
補助者のログイン情報およびプロフィールを管理します。

| カラム名 | 型 | 制約 | 説明 |
| :--- | :--- | :--- | :--- |
| `id` | INT | PRIMARY KEY AUTO_INCREMENT | ユーザーID |
| `login_id` | VARCHAR(255) | UNIQUE, NOT NULL | 電話番号またはメールアドレス |
| `password_hash` | VARCHAR(255) | NOT NULL | ハッシュ化されたパスワード |
| `user_name` | VARCHAR(100) | | 表示名（「名前の設定」用） |
| `created_at` | DATETIME | DEFAULT CURRENT_TIMESTAMP | 登録日時 |

##### 2.2 `recognition_logs` (認識・対話ログ)
Gemini APIによる解析結果の全履歴です。画面の「log」セクションに表示されます。

| カラム名 | 型 | 制約 | 説明 |
| :--- | :--- | :--- | :--- |
| `id` | INT | PRIMARY KEY AUTO_INCREMENT | ログID |
| `timestamp` | DATETIME | DEFAULT CURRENT_TIMESTAMP | 発生日時 |
| `image_path` | VARCHAR(500) | | サーバー上の画像保存先パス |
| `user_query` | TEXT | | 音声認識された質問内容 |
| `ai_response` | TEXT | | AIが生成した回答内容 |
| `is_emergency` | TINYINT(1) | DEFAULT 0 | 緊急判定（1:緊急, 0:通常） |

##### 2.3 `notification_history` (通知・行動履歴)
家族へのLINE通知内容や、画面上の「行動の履歴」を表示するためのデータです。

| カラム名 | 型 | 制約 | 説明 |
| :--- | :--- | :--- | :--- |
| `id` | INT | PRIMARY KEY AUTO_INCREMENT | 通知ID |
| `timestamp` | DATETIME | DEFAULT CURRENT_TIMESTAMP | 通知日時 |
| `category` | VARCHAR(50) | | 通知種別（薬、転倒予兆、生存確認等） |
| `message` | TEXT | | 通知メッセージの内容 |
| `is_read` | TINYINT(1) | DEFAULT 0 | 既読フラグ（1:既読, 0:未読） |

##### 2.4 `system_settings` (システム設定)
「通知設定」や「キーワード設定」など、画面から変更可能な各種パラメータです。

| カラム名 | 型 | 制約 | 説明 |
| :--- | :--- | :--- | :--- |
| `setting_key` | VARCHAR(100) | PRIMARY KEY | 設定キー名 |
| `setting_value` | TEXT | | 設定値 |
| `category` | VARCHAR(50) | | 設定分類（alert, user, api等） |
| `updated_at` | DATETIME | ON UPDATE CURRENT_TIMESTAMP | 最終更新日時 |

---
