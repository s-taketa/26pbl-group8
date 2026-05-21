
---

### データベース設計書 (SQLite)

#### 1. 概要
本システムでは、認識イベントやシステムログを軽量に保存するため、**SQLite**を採用します。これにより、運用後の振り返りや解析が可能になります。

#### 2. テーブル定義

##### 2.1 `recognition_logs` (認識・対話ログ)
要介護者からの質問内容、AIの回答、およびその際の画像パスを保存します。

| カラム名 | 型 | 制約 | 説明 |
| :--- | :--- | :--- | :--- |
| `id` | INTEGER | PRIMARY KEY AUTOINCREMENT | ログID |
| `timestamp` | DATETIME | DEFAULT CURRENT_TIMESTAMP | 発生日時 |
| `image_path` | TEXT | | 質問時の保存画像パス（「リアルタイム画像or認識した画像」） |
| `user_query` | TEXT | | 聞かれた内容 |
| `ai_response` | TEXT | | 生成した回答 |

##### 2.2 `system_status` (システム状態)
システムの稼働状況や通知設定などを保持します。

| カラム名 | 型 | 制約 | 説明 |
| :--- | :--- | :--- | :--- |
| `setting_name` | TEXT | PRIMARY KEY | 設定項目（通知設定、名前の設定など） |
| `value` | TEXT | | 設定値 |
| `updated_at` | DATETIME | | 最終更新日時 |

---