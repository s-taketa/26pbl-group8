# server/main.py（サーバー側のFlaskアプリ本体）

from flask import Flask, request, jsonify, session
from PIL import Image
import io
import os
import uuid

from ai_logic import processResponse
from main_controller import MainController
# from database import DatabaseManager   # ← DB担当が実装予定。実装完了後にコメント解除
# from line_notifier import send_line_alert   # 浅尾さん担当（緊急通知）

app = Flask(__name__)
app.secret_key = "change-this-secret-key"  # 本番では環境変数化すること

controller = MainController()
# db_manager = DatabaseManager()   # ← DB担当の実装完了後にコメント解除

IMAGE_STORAGE_DIR = "/app/images"


# ==================== AI連携エンドポイント（自分の担当） ====================

@app.route('/api/recognition', methods=['POST'])
def receive_recognition():
    """
    ラズパイから画像とコマンド（テキスト）を受け取り、
    Gemini APIで解析した結果を返すエンドポイント。

    受信形式: multipart/form-data
      - image  : 画像ファイル（capture.jpg）
      - command: 利用者の発話テキスト

    返却形式: JSON
      {"answer_text": "..."}
    """
    if "image" not in request.files:
        return jsonify({"status": "error", "message": "画像が含まれていません"}), 400

    command = request.form.get("command")
    if not command:
        return jsonify({"status": "error", "message": "commandが指定されていません"}), 400

    image_file = request.files["image"]
    print(f"[RECV] 画像受信: {image_file.filename}")
    print(f"[RECV] コマンド受信: 「{command}」")

    try:
        image_bytes = image_file.read()
        image = Image.open(io.BytesIO(image_bytes))

        # --- 画像をストレージに保存（ファイル名の重複を避けてUUID付与） ---
        os.makedirs(IMAGE_STORAGE_DIR, exist_ok=True)
        saved_filename = f"{uuid.uuid4().hex}_{image_file.filename}"
        saved_path = os.path.join(IMAGE_STORAGE_DIR, saved_filename)
        with open(saved_path, "wb") as f:
            f.write(image_bytes)

        # --- Gemini APIで解析 ---
        result = processResponse(image, command)
        print(f"[AI] 解析結果: {result}")

        # --- 緊急時はLINE通知をトリガー ---
        if result.get("is_emergency") == 1:
            print(f"[ALERT] 緊急検知: {result.get('category')} - {result.get('alert_message')}")
            # send_line_alert(result)   # ← line_notifier.py 実装完了後にコメント解除

        # --- DB保存（DB担当の実装完了後にコメント解除） ---
        # log_entry = {
        #     "user_id": 1,
        #     "image_path": saved_path,
        #     "user_query": command,
        #     "ai_response": result.get("answer"),
        #     "is_emergency": result.get("is_emergency"),
        #     "category": result.get("category"),
        #     "alert_message": result.get("alert_message"),
        # }
        # db_manager.writeRecognitionLog(log_entry)
        print(f"[DB] (未実装のためスキップ) 保存予定だったログ: query={command}, answer={result.get('answer')}")

        # --- ラズパイへ回答テキストを返す ---
        return jsonify({"answer_text": result.get("answer")})

    except Exception as e:
        print(f"[ERROR] 処理中にエラー: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500


@app.route('/api/heartbeat', methods=['GET'])
def heartbeat():
    """heartbeatCheck() 対応エンドポイント。ラズパイからの死活確認に200を返すだけ。"""
    return jsonify({"status": "ok"}), 200


# ==================== 認証・管理エンドポイント（MainController担当） ====================

@app.route('/api/login', methods=['POST'])
def login():
    data = request.get_json()
    user_id = data.get("id")
    password = data.get("password")

    success = controller.authenticateUser(user_id, password)
    if success:
        session["user_id"] = user_id
        return jsonify({"status": "ok"})
    return jsonify({"status": "error", "message": "認証失敗"}), 401


@app.route('/api/send-auth-code', methods=['POST'])
def send_auth_code():
    controller.sendAuthCode()
    return jsonify({"status": "ok", "message": "認証コードを送信しました"})


@app.route('/api/validate-auth-code', methods=['POST'])
def validate_auth_code():
    data = request.get_json()
    code = data.get("code")
    is_valid = controller.validateAuthCode(code)
    if is_valid:
        return jsonify({"status": "ok"})
    return jsonify({"status": "error", "message": "コードが正しくありません"}), 400


@app.route('/api/reset-password', methods=['POST'])
def reset_password():
    controller.resetPassword()
    return jsonify({"status": "ok", "message": "パスワードを更新しました"})


@app.route('/api/dashboard', methods=['GET'])
def dashboard():
    data = controller.getDashboardData()
    return jsonify(data)


@app.route('/api/sync-settings', methods=['POST'])
def sync_settings():
    controller.syncSettingsToEdge()
    return jsonify({"status": "ok", "message": "ラズパイへ設定を反映しました"})


# ==================== 起動処理 ====================

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)