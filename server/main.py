# server/main.py
from flask import Flask, request, jsonify
from database import DatabaseManager  # パッケージを指定して読み込む

app = Flask(__name__)
db = DatabaseManager()  # 司令塔専用のDB操作窓口を開設

class MainController:

    """管理・認証を扱うサーバーサイドのメインクラス"""

    # 管理・認証を扱うサーバーサイドのメインクラス（チームメンバーの設計）


    def authenticateUser(self, login_id, password_hash):
        """ログインIDとパスワードの照合"""
        user = db.getUserByEmail(login_id)
        if user and user.password_hash == password_hash:
            return True, user.user_name
        return False, None

    def getDashboardData(self):
        """フロントエンド用：最新ログの取得"""
        logs = db.getRecognitionHistory(limit=5)
        return [{"query": log.user_query, "response": log.ai_response} for log in logs]

# --- APIエンドポイント ---


@app.route('/login', methods=['POST'])
def login():
    data = request.json
    controller = MainController()
    success, name = controller.authenticateUser(data['login_id'], data['password_hash'])
    return jsonify({"success": success, "user_name": name})

@app.route('/dashboard', methods=['GET'])
def dashboard():
    controller = MainController()
    return jsonify(controller.getDashboardData())

    def sendRecognitionCommand(self):
        # 司令塔としてエッジ（ラズパイ）に認識開始の命令を出す
        pass


@app.route('/')
def hello():
    return "見守りサーバー起動成功！データベース連携の準備完了です！"

if __name__ == '__main__':
    print("見守りサーバー（司令塔）を起動しています...")
    app.run(host='0.0.0.0', port=5000)


