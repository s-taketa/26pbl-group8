# API仕様書 — コエミマ

| 項目 | 内容 |
|---|---|
| バージョン | 2.1 |
| 更新日 | 2026-07-09 |
| ベースURL（サーバー） | `http://<サーバーIP>:5000` |
| ベースURL（エッジ） | `http://<PiのIP>:5002` |

---

## 1. サーバー API（`server/main.py`）

### 1.1 認識・連携

#### POST `/api/recognition` 🔒
エッジから画像とコマンドを受け取り、AI解析後に「回答テキスト＋文ごとの音声」をストリーミング返却する。`EDGE_API_TOKEN` 設定時はヘッダ `X-Edge-Token` の一致が必要。

- **リクエスト**：`multipart/form-data`
  - `image`：画像ファイル（capture.jpg）
  - `command`：利用者の発話テキスト
- **レスポンス**：`application/octet-stream`（フレーム連結）
  - 各フレーム = `4バイト長(BE)` + `本体`
  - 1フレーム目：メタJSON `{"answer_text": "...", "is_emergency": 0}`
  - 2フレーム目以降：文ごとの VOICEVOX 合成 WAV
  - ※ 音声合成が無効な環境では後方互換で `{"answer_text": "..."}`（JSON）を返す
- **副作用**：認識ログをDB保存。緊急時は LINE 通知＋通知履歴保存。会話ログ送信ONなら通常時もLINE送信。
- **エラー**：`400`（image/command 不足）、`401`（トークン不一致）、`500`（AI解析失敗等）

#### GET `/api/heartbeat`
死活確認。`200 {"status":"ok"}`。

#### GET `/api/edge-config` 🔒
エッジ設定を返す。`200 {"keyword":"チャピー,起動して"}`。`EDGE_API_TOKEN` 設定時はヘッダ `X-Edge-Token` が必要（不一致は401）。

> 🔒＝`EDGE_API_TOKEN` 環境変数を設定した場合のみ認証が要求される（未設定時は後方互換のため無認証）。

### 1.2 認証・アカウント（★＝レート制限あり：同一IPから5分間に既定5〜10回まで）

| メソッド | パス | 概要 | リクエスト | レスポンス |
|---|---|---|---|---|
| POST ★ | `/api/login` | ログイン（メール2段階対応） | `{id, password}` | `{status:"ok"}` / `{status:"code_sent"}` / 401 |
| POST ★ | `/api/login-verify` | ログイン確認コード検証 | `{code}` | `{status:"ok"}` / 400 |
| POST ★ | `/api/register` | 新規登録（メール宛は確認コード送信） | `{id, password, name}` | `{status:"ok"}` / `{status:"code_sent"}` / 400 |
| POST ★ | `/api/register-verify` | 新規登録の確認コード検証・本登録 | `{id, code}` | `{status:"ok"}` / 400 |
| POST ★ | `/api/send-auth-code` | 認証コード送信 | `{contact}` | `{status:"ok"}` |
| POST ★ | `/api/validate-auth-code` | 認証コード検証（成功で再設定を許可） | `{contact, code}` | `{status:"ok"}` / 400 |
| POST ★ | `/api/reset-password` | パスワード再設定 | `{id, password}` | `{status:"ok"}` / 400 / **403** |

> メール2段階：`login_id` がメール形式かつ SMTP 設定済みのとき `code_sent` を返し、`/api/login-verify` で確定。未設定時は1段階でログイン。
> 新規登録：メール宛かつSMTP設定済みの場合は `code_sent` を返し、`/api/register-verify` でコード検証後にアカウントを作成する（他人のメールアドレスでの登録を防止）。未設定時は即時登録。
> パスワード再設定：`/api/validate-auth-code` でコード検証に成功した宛先のみ `/api/reset-password` を許可する（宛先不一致は **403**）。
> レート制限超過時は **429** を返す。

### 1.3 データ・設定（★＝ログイン必須。未ログインは 401）

| メソッド | パス | 概要 | レスポンス |
|---|---|---|---|
| GET ★ | `/api/dashboard` | 認識ログ一覧（最新20件） | `[{timestamp, query, response, is_emergency, image_url}, ...]` |
| GET ★ | `/api/settings` | 設定取得 | `{notify_conversation_log, notify_periodic, keyword, user_name}` |
| POST ★ | `/api/settings` | 設定保存 | `{status:"ok"}` |
| POST ★ | `/api/sync-settings` | エッジへ設定反映 | `{status:"ok"}` |
| GET ★ | `/images/<filename>` | 認識画像配信 | 画像バイナリ / 403 |

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
| GET | `/video` 🔒 | リアルタイム映像（MJPEGストリーム）。`EDGE_API_TOKEN` 設定時はクエリ `?token=` が必要 |
| POST | `/command` 🔒 | サーバーからの命令受付（`{action:"start_recognition"}` / `{action:"stop"}`）。`EDGE_API_TOKEN` 設定時はヘッダ `X-Edge-Token` が必要 |

エッジは能動的に以下も行う（`EDGE_API_TOKEN` 設定時はいずれもヘッダ `X-Edge-Token` を付与）：
- `GET <server>/api/heartbeat` を定期送信（死活監視）
- `GET <server>/api/edge-config` でウェイクワードを取得・同期
- `POST <server>/api/recognition` に画像＋コマンドを送信

ダッシュボードの映像表示（`<img>` タグ）はブラウザから直接 `/video` を取得するため、トークンはURLのクエリ文字列で渡す（サーバーがログイン中の画面にのみ埋め込む）。

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
