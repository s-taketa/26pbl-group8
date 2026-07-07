# server/main.py（サーバー側のFlaskアプリ本体）
import io
import os
import json
import time
import uuid
import struct
import threading

from flask import (Flask, request, jsonify, session, Response,
                   render_template, redirect, url_for, send_from_directory)
from PIL import Image

# ---- 依存モジュール（無い場合もサーバーが起動できるようフォールバック） ----
try:
    from database import DatabaseManager
    db = DatabaseManager()
except Exception as e:
    print(f"[WARN] DB初期化に失敗（DBなしで継続）: {e}")
    db = None

try:
    from ai_logic import processResponse
except Exception as e:
    print(f"[WARN] ai_logic 読み込み失敗（ダミー応答で継続）: {e}")
    def processResponse(image, command):
        return {"answer": "（AI未接続）状況を確認できません。", "is_emergency": 0,
                "category": "", "alert_message": ""}

try:
    from voice_handler import VoiceHandler
    voice_handler = VoiceHandler()
except Exception as e:
    print(f"[WARN] VoiceHandler 読み込み失敗（音声合成なしで継続）: {e}")
    voice_handler = None

try:
    from line_notifier import LineNotifier
    line_notifier = LineNotifier()
except Exception as e:
    print(f"[WARN] LINE通知は無効（LINE_TOKEN未設定など）: {e}")
    line_notifier = None

try:
    import mailer
except Exception as e:
    print(f"[WARN] mailer 読み込み失敗（メール認証なしで継続）: {e}")
    mailer = None

from main_controller import MainController

# ---- Flask 初期化（templates/static はリポジトリ直下にある） ----
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
app = Flask(
    __name__,
    template_folder=os.path.join(BASE_DIR, "..", "templates"),
    static_folder=os.path.join(BASE_DIR, "..", "static"),
)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-this-secret-key")

IMAGE_STORAGE_DIR = os.getenv("IMAGE_STORAGE_DIR", "/app/images")
DEFAULT_USER_ID = 1  # 初期ユーザー（init_dbでseed）

controller = MainController(db=db)


def _frame(payload: bytes) -> bytes:
    """ストリーム1フレーム = 4バイトの長さ接頭辞(BE) + 本体"""
    return struct.pack(">I", len(payload)) + payload


def _emergency_flag(v) -> int:
    """is_emergency を 0/1 に正規化する。
    Geminiが 1 / "1" / True / "true" のどれで返しても緊急として扱う。
    （以前は `== 1` だけで判定しており、"1"（文字列）だと通知が漏れていた）"""
    if isinstance(v, bool):
        return 1 if v else 0
    try:
        return 1 if int(v) == 1 else 0
    except (TypeError, ValueError):
        return 1 if str(v).strip().lower() in ("1", "true", "yes") else 0


def _ui_context():
    """画面テンプレート共通のコンテキスト（表示名など）。"""
    name = "管理者"
    try:
        name = controller.getSettings().get("user_name") or "管理者"
    except Exception:
        pass
    return {"user_name": name}


def periodic_notifier():
    """『定期的な通知』がONのとき、一定間隔で見守り状況をLINE送信する。"""
    interval = int(os.getenv("PERIODIC_NOTIFY_MINUTES", "60")) * 60
    while True:
        time.sleep(interval)
        try:
            if not line_notifier:
                continue
            settings = controller.getSettings()
            if settings.get("notify_periodic") != "1":
                continue
            rows = controller.getDashboardData()
            if rows:
                latest = rows[0]
                msg = f"【見守り状況】稼働中です。直近の確認:「{latest['query']}」（{latest['timestamp']}）"
            else:
                msg = "【見守り状況】稼働中です。直近の記録はまだありません。"
            line_notifier.sendLineNotification(msg)
            print("[PERIODIC] 定期通知を送信しました")
        except Exception as e:
            print(f"[PERIODIC] 定期通知失敗: {e}")


# ==================== AI連携エンドポイント ====================
@app.route('/api/recognition', methods=['POST'])
def receive_recognition():
    """
    ラズパイから画像とコマンド（テキスト）を受け取り、Geminiで解析し、
    DB保存・緊急時LINE通知を行ったうえで「回答テキスト＋文ごとの音声」を
    フレームストリーム（application/octet-stream）で返す。
      各フレーム = 4バイト長(BE) + 本体
        1フレーム目 : メタJSON {"answer_text": "...", "is_emergency": 0}
        2フレーム目〜: 文ごとのVOICEVOX合成WAV
    （VoiceHandlerが無い環境では従来通り JSON {"answer_text": "..."} を返す）
    """
    if "image" not in request.files:
        return jsonify({"status": "error", "message": "画像が含まれていません"}), 400

    command = request.form.get("command")
    if not command:
        return jsonify({"status": "error", "message": "commandが指定されていません"}), 400

    image_file = request.files["image"]
    print(f"[RECV] 画像受信: {image_file.filename} / コマンド: 「{command}」")

    try:
        image_bytes = image_file.read()
        image = Image.open(io.BytesIO(image_bytes))

        # 画像をストレージに保存（UUID付与）
        os.makedirs(IMAGE_STORAGE_DIR, exist_ok=True)
        saved_filename = f"{uuid.uuid4().hex}_{image_file.filename}"
        saved_path = os.path.join(IMAGE_STORAGE_DIR, saved_filename)
        with open(saved_path, "wb") as f:
            f.write(image_bytes)

        # AI解析
        result = processResponse(image, command)
        print(f"[AI] 解析結果: {result}")

        # 緊急フラグを 0/1 に正規化（型ゆらぎで通知漏れ／誤検知を防ぐ）
        emergency = _emergency_flag(result.get("is_emergency"))

        # 認識ログの紐付け先ユーザー（初期アカウント固定ではなく実在する先頭ユーザー）
        uid = db.getFirstUserId() if db else None

        # DB保存（認識ログ）
        if db and uid:
            try:
                db.writeRecognitionLog({
                    "user_id": uid,
                    "image_path": saved_path,
                    "user_query": command,
                    "ai_response": result.get("answer"),
                    "is_emergency": bool(emergency),
                })
            except Exception as e:
                print(f"[WARN] DB保存失敗: {e}")

        # 通知設定を取得
        settings = controller.getSettings() if controller else {}
        answer_text = result.get("answer", "") or ""

        if emergency == 1:
            # 緊急時：LINE緊急通知 ＋ 通知履歴保存
            category = result.get("category") or "other_emergency"
            alert = result.get("alert_message") or answer_text or "緊急事態を検知しました"
            print(f"[ALERT] 緊急検知: {category} - {alert}")
            if line_notifier:
                try:
                    line_notifier.sendUrgentAlert(alert, "high")
                except Exception as e:
                    print(f"[WARN] LINE通知失敗: {e}")
            if db and uid:
                try:
                    db.writeNotificationHistory({
                        "user_id": uid, "category": category, "message": alert,
                    })
                except Exception as e:
                    print(f"[WARN] 通知履歴保存失敗: {e}")
        elif line_notifier and settings.get("notify_conversation_log") == "1":
            # 緊急以外でも「会話ログ送信」がONなら家族へLINE送信
            try:
                line_notifier.sendLineNotification(f"【会話ログ】\nQ: {command}\nA: {answer_text}")
            except Exception as e:
                print(f"[WARN] 会話ログLINE送信失敗: {e}")

    except Exception as e:
        print(f"[ERROR] 処理中にエラー: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

    answer = result.get("answer", "") or ""

    # 音声合成が使えない場合は後方互換でJSONを返す
    if voice_handler is None:
        return jsonify({"answer_text": answer})

    # 「回答テキスト＋文ごとの音声」をストリーミング返却
    def generate():
        meta = json.dumps(
            {"answer_text": answer, "is_emergency": emergency},
            ensure_ascii=False,
        ).encode("utf-8")
        yield _frame(meta)
        for index, wav in enumerate(voice_handler.synthesize_stream(answer), start=1):
            print(f"[TTS] 第{index}文を送信 ({len(wav)} bytes)")
            yield _frame(wav)

    return Response(generate(), mimetype="application/octet-stream")


@app.route('/api/heartbeat', methods=['GET'])
def heartbeat():
    """ラズパイからの死活確認に200を返すだけ。"""
    return jsonify({"status": "ok"}), 200


# ==================== 認証・管理エンドポイント ====================
@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json(force=True, silent=True) or {}
    login_id = data.get("id")

    # 1段階目：ID/パスワード照合
    if not controller.authenticateUser(login_id, data.get("password")):
        return jsonify({"status": "error", "message": "IDまたはパスワードが正しくありません"}), 401

    # 2段階目：メール宛かつSMTP設定済みなら、確認コードを送って保留にする
    if mailer and mailer.is_email(login_id) and mailer.is_configured():
        controller.sendAuthCode(login_id)
        session["pending_login"] = login_id
        return jsonify({"status": "code_sent", "message": "確認コードをメールに送信しました"})

    # メール認証が使えない場合（メール以外のID/未設定）はそのままログイン
    session["user_id"] = login_id
    return jsonify({"status": "ok"})


@app.route('/api/login-verify', methods=['POST'])
def api_login_verify():
    """ログイン時のメール確認コードを検証してログインを確定する。"""
    data = request.get_json(force=True, silent=True) or {}
    pending = session.get("pending_login")
    if not pending:
        return jsonify({"status": "error", "message": "セッションが無効です。最初からやり直してください"}), 400
    if controller.validateAuthCode(data.get("code"), pending):
        session.pop("pending_login", None)
        session["user_id"] = pending
        return jsonify({"status": "ok"})
    return jsonify({"status": "error", "message": "確認コードが正しくないか、期限が切れています"}), 400


@app.route('/api/register', methods=['POST'])
def api_register():
    data = request.get_json(force=True, silent=True) or {}
    ok, message = controller.registerUser(
        data.get("id"), data.get("password"), data.get("name"))
    if ok:
        return jsonify({"status": "ok", "message": message})
    return jsonify({"status": "error", "message": message}), 400


@app.route('/api/send-auth-code', methods=['POST'])
def send_auth_code():
    data = request.get_json(force=True, silent=True) or {}
    controller.sendAuthCode(data.get("contact"))
    return jsonify({"status": "ok", "message": "認証コードを送信しました"})


@app.route('/api/validate-auth-code', methods=['POST'])
def validate_auth_code():
    data = request.get_json(force=True, silent=True) or {}
    if controller.validateAuthCode(data.get("code"), data.get("contact")):
        return jsonify({"status": "ok"})
    return jsonify({"status": "error", "message": "コードが正しくありません"}), 400


@app.route('/api/reset-password', methods=['POST'])
def reset_password():
    data = request.get_json(force=True, silent=True) or {}
    ok = controller.resetPassword(data.get("id"), data.get("password"))
    if ok:
        return jsonify({"status": "ok", "message": "パスワードを更新しました"})
    return jsonify({"status": "error", "message": "パスワード更新に失敗しました"}), 400


@app.route('/api/dashboard', methods=['GET'])
def dashboard_data():
    return jsonify(controller.getDashboardData())


@app.route('/api/settings', methods=['GET'])
def api_get_settings():
    return jsonify(controller.getSettings())


@app.route('/api/settings', methods=['POST'])
def api_save_settings():
    data = request.get_json(force=True, silent=True) or {}
    if controller.updateSettings(data):
        return jsonify({"status": "ok", "message": "設定を保存しました"})
    return jsonify({"status": "error", "message": "保存に失敗しました"}), 400


@app.route('/api/sync-settings', methods=['POST'])
def sync_settings():
    controller.syncSettingsToEdge()
    return jsonify({"status": "ok", "message": "ラズパイへ設定を反映しました"})


@app.route('/api/edge-config', methods=['GET'])
def edge_config():
    """エッジ(Pi)が取得する設定。ウェイクワードなどを返す。"""
    settings = controller.getSettings()
    return jsonify({"keyword": settings.get("keyword", "チャピー")})


# ==================== 画面（フロントエンド） ====================
@app.route('/')
def index():
    if not session.get("user_id"):
        return redirect(url_for("login_page"))
    # エッジ(Pi)のリアルタイム映像URL。.env の EDGE_URL（例: http://192.168.100.15:5002）。
    return render_template("index.html", edge_url=os.getenv("EDGE_URL", ""), **_ui_context())


@app.route('/login')
def login_page():
    return render_template("login.html")


@app.route('/register')
def register_page():
    return render_template("register.html")


@app.route('/forgot')
def forgot_page():
    return render_template("forgot.html")


@app.route('/logs')
def logs_page():
    if not session.get("user_id"):
        return redirect(url_for("login_page"))
    return render_template("logs.html", **_ui_context())


@app.route('/settings')
def settings_page():
    if not session.get("user_id"):
        return redirect(url_for("login_page"))
    return render_template("settings.html", **_ui_context())


@app.route('/images/<path:filename>')
def serve_image(filename):
    """認識時に保存した画像を配信する（ログイン必須）。"""
    if not session.get("user_id"):
        return ("", 403)
    return send_from_directory(IMAGE_STORAGE_DIR, filename)


@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for("login_page"))


# ==================== 起動処理 ====================
if __name__ == "__main__":
    if db:
        try:
            # 初期アカウントは作らない（テーブル作成のみ）
            db.init_db(seed_default_user=False)
            print("[DB] テーブル初期化 完了")
        except Exception as e:
            print(f"[WARN] DB初期化スキップ（MySQL未起動など）: {e}")

    # 定期通知スレッドを起動（設定ONのときだけ実際に送信）
    threading.Thread(target=periodic_notifier, daemon=True).start()
    print("[SYSTEM] 定期通知スレッドを起動しました")

    app.run(host="0.0.0.0", port=5000)
