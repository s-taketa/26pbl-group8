# API仕様書 — コエミマ

| 項目 | 内容 |
|---|---|
| バージョン | 2.0 |
| 更新日 | 2026-07-09 |
| ベースURL（サーバー） | `http://<サーバーIP>:5000` |
| ベースURL（エッジ） | `http://<PiのIP>:5002` |

---

## 1. サーバー API（`server/main.py`）

### 1.1 認識・連携

#### POST `/api/recognition`
エッジから画像とコマンドを受け取り、AI解析後に「回答テキスト＋文ごとの音声」をストリーミング返却する。

- **リクエスト**：`multipart/form-data`
  - `image`：画像ファイル（capture.jpg）
  - `command`：利用者の発話テキスト
- **レスポンス**：`application/octet-stream`（フレーム連結）
  - 各フレーム = `4バイト長(BE)` + `本体`
  - 1フレーム目：メタJSON `{"answer_text": "...", "is_emergency": 0}`
  - 2フレーム目以降：文ごとの VOICEVOX 合成 WAV
  - ※ 音声合成が無効な環境では後方互換で `{"answer_text": "..."}`（JSON）を返す
- **副作用**：認識ログをDB保存。緊急時は LINE 通知＋通知履歴保存。会話ログ送信ONなら通常時もLINE送信。
- **エラー**：`400`（image/command 不足）、`500`（AI解析失敗等）

#### GET `/api/heartbeat`
死活確認。`200 {"status":"ok"}`。

#### GET `/api/edge-config`
エッジ設定を返す。`200 {"keyword":"チャピー,起動して"}`。

### 1.2 認証・アカウント

| メソッド | パス | 概要 | リクエスト | レスポンス |
|---|---|---|---|---|
| POST | `/api/login` | ログイン（メール2段階対応） | `{id, password}` | `{status:"ok"}` / `{status:"code_sent"}` / 401 |
| POST | `/api/login-verify` | ログイン確認コード検証 | `{code}` | `{status:"ok"}` / 400 |
| POST | `/api/register` | 新規登録 | `{id, password, name}` | `{status:"ok"}` / 400 |
| POST | `/api/send-auth-code` | 認証コード送信 | `{contact}` | `{status:"ok"}` |
| POST | `/api/validate-auth-code` | 認証コード検証 | `{contact, code}` | `{status:"ok"}` / 400 |
| POST | `/api/reset-password` | パスワード再設定 | `{id, password}` | `{status:"ok"}` / 400 |

> メール2段階：`login_id` がメール形式かつ SMTP 設定済みのとき `code_sent` を返し、`/api/login-verify` で確定。未設定時は1段階でログイン。

### 1.3 データ・設定

| メソッド | パス | 概要 | レスポンス |
|---|---|---|---|
| GET | `/api/dashboard` | 認識ログ一覧（最新20件） | `[{timestamp, query, response, is_emergency, image_url}, ...]` |
| GET | `/api/settings` | 設定取得 | `{notify_conversation_log, notify_periodic, keyword, user_name}` |
| POST | `/api/settings` | 設定保存 | `{status:"ok"}` |
| POST | `/api/sync-settings` | エッジへ設定反映 | `{status:"ok"}` |
| GET | `/images/<filename>` | 認識画像配信（要ログイン） | 画像バイナリ / 403 |

### 1.4 画面（HTML）
| パス | 画面 |
|---|---|
| `/` | ダッシュボード（未ログインは `/login` へ） |
| `/login` | ログイン |
| `/register` | 新規登録 |
| `/forgot` | パスワード再設定（3ステップ） |
| `/logs` | 履歴ログ |
| `/settings` | 通知・詳細設定 |
| `/logout` | ログアウト |

---

## 2. エッジ API（`edge/app.py`）

| メソッド | パス | 概要 |
|---|---|---|
| GET | `/` | 簡易映像ビューア |
| GET | `/video` | リアルタイム映像（MJPEGストリーム） |
| POST | `/command` | サーバーからの命令受付（`{action:"start_recognition"}` / `{action:"stop"}`） |

エッジは能動的に以下も行う：
- `GET <server>/api/heartbeat` を定期送信（死活監視）
- `GET <server>/api/edge-config` でウェイクワードを取得・同期
- `POST <server>/api/recognition` に画像＋コマンドを送信

---

## 3. 補足：ストリーミング音声プロトコル
`/api/recognition` の返却は独自のフレーム連結ストリーム。
```
[4バイト長(BE)][メタJSON(UTF-8)]
[4バイト長(BE)][WAV 1文目]
[4バイト長(BE)][WAV 2文目]
...
```
エッジ側は長さ接頭辞を読んで1フレームずつ取り出し、WAVを届いた順に `aplay` で再生する。
