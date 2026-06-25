# server/main.py
from flask import Flask, request, jsonify, session
from PIL import Image
import io
import os
import uuid

# 追加ユーティリティ（オプション）
try:
    import struct
    import json
except Exception:
    struct = None
    json = None

# DB とコントローラ（存在しない場合は簡易フォールバック）
try:
    from database import DatabaseManager
    db = DatabaseManager()
except Exception:
    db = None
    def _dummy_get_recognition_history(limit=5):
        return []
    class DatabaseManager:
        def getRecognitionHistory(self, limit=5):
            return _dummy_get_recognition_history(limit)

# AI ロジック（存在しない場合はフォールバック）
try:
    from ai_logic import processResponse
except Exception:
    def processResponse(image, command):
        return {"answer": "（AI未実装）", "is_emergency": 0, "category": None, "alert_message": None}

# VoiceHandler（存在しない場合は無視）
try:
    from voice_handler import VoiceHandler
    voice_handler = VoiceHandler()
except Exception:
    voice_handler = None

app = Flask(__name__)
app.secret_key = os.getenv("FLASK_SECRET_KEY", "change-this-secret-key")
IMAGE_STORAGE_DIR = os.getenv("IMAGE_STORAGE_DIR", "/app/images")

class MainController:
    # 管理・認証を扱うサーバーサイドのメインクラス

    def authenticateUser(self, login_id, password_hash):
        """ログインIDとパスワードの照合"""
        if db:
            user = db.getUserByEmail(login_id)
            if user and user.password_hash == password_hash:
                return True
        return False

    def getDashboardData(self):
        # フロントエンド用：最新ログの取得
        if db:
            logs = db.getRecognitionHistory(limit=5)
            return [{"query": log.user_query, "response": log.ai_response} for log in logs]
        return []

    # スタブ実装
    def sendAuthCode(self):
        pass
    def validateAuthCode(self, code):
        return True
    def resetPassword(self):
        pass
    def syncSettingsToEdge(self):
        pass
    def sendRecognitionCommand(self):
        pass

controller = MainController()

# ==================== AI連携エンドポイント ====================
@app.route('/api/recognition', methods=['POST'])
def receive_recognition():
    """
    ラズパイから画像とコマンド（テキスト）を受け取り、解析した結果を返す（JSON）。
    受信形式: multipart/form-data
      - image  : 画像ファイル（capture.jpg）
      - command: 利用者の発話テキスト
    返却形式: JSON {"answer_text": "..."}
    """
    if "image" not in request.files:
        return jsonify({"status": "error", "message": "画像が含まれていません"}), 400

    command = request.form.get("command")
    if not command:
        return jsonify({"status": "error", "message": "commandが指定されていません"}), 400

    image_file = request.files["image"]
    try:
        image_bytes = image_file.read()
        image = Image.open(io.BytesIO(image_bytes))

        # 画像をストレージに保存（UUID付与）
        os.makedirs(IMAGE_STORAGE_DIR, exist_ok=True)
        saved_filename = f"{uuid.uuid4().hex}_{image_file.filename}"
        saved_path = os.path.join(IMAGE_STORAGE_DIR, saved_filename)
        with open(saved_path, "wb") as f:
            f.write(image_bytes)

        # AI 解析
        result = processResponse(image, command)

        # 緊急時はログ出力／通知トリガー（line_notifier 実装後に連携）
        if result.get("is_emergency") == 1:
            print(f"[ALERT] 緊急検知: {result.get('category')} - {result.get('alert_message')}")
            # TODO: send LINE 等の外部通知を行う

        """
	DB 保存（DB の実装に応じて有効化）
        if db:
            log_entry = {
                "user_id": 1,
                "image_path": saved_path,
                "user_query": command,
                "ai_response": result.get("answer"),
                "is_emergency": result.get("is_emergency"),
            }
            db.writeRecognitionLog(log_entry)
	"""

        return jsonify({"answer_text": result.get("answer")})
    except Exception as e:
        print(f"[ERROR] 処理中にエラー: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route('/api/heartbeat', methods=['GET'])
def heartbeat():
    # heartbeatCheck() 対応エンドポイント。ラズパイからの死活確認に200を返すだけ。
    return jsonify({"status": "ok"}), 200

# ==================== 認証・管理エンドポイント ====================
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

@app.route('/')
def hello():
    return "見守りサーバー起動成功！データベース連携の準備完了です！"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)