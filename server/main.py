# server/main.py
from flask import Flask

# Webサーバーを立ち上げてコンテナを死なせないためのエンジン
app = Flask(__name__)

class MainController:
    # 管理・認証を扱うサーバーサイドのメインクラス（チームメンバーの設計）

    def authenticateUser(self, id, password):
        pass

    def sendAuthCode(self):
        pass

    def validateAuthCode(self, code):
        pass

    def resetPassword(self):
        pass

    def getDashboardData(self):
        pass

    def syncSettingsToEdge(self):
        pass

    def sendRecognitionCommand(self):
        # 司令塔としてエッジ（ラズパイ）に認識開始の命令を出す
        pass

# サーバーの稼働確認用のWebページ
@app.route('/')
def hello():
    return "見守りサーバー起動成功！データベース連携の準備完了です！"

# コンテナ起動時にここが実行され、サーバーが「待機状態（帰宅しない）」になります
if __name__ == '__main__':
    print("見守りサーバー（司令塔）を起動しています...")
    app.run(host='0.0.0.0', port=5000)


