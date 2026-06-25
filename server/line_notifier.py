import os
<<<<<<< HEAD
from linebot import LineBotApi
from linebot.models import TextSendMessage
=======
import requests

>>>>>>> main

class LineNotifier:
    # 外部連携
     """
    家族へのLINE通知およびトークンの検証を担当するクラス
    """
def __init__(self):
        # .envから情報を読み込む (ソース[3], [4]に基づく)
        self.channel_access_token = os.getenv('LINE_CHANNEL_ACCESS_TOKEN')
        self.user_id = os.getenv('LINE_USER_ID')
        
        if self.channel_access_token:
            self.line_bot_api = LineBotApi(self.channel_access_token)
        else:
            self.line_bot_api = None

<<<<<<< HEAD
def validateLineToken(self, token):
        # LINE API トークンの有効性確認
        #LINE API トークンの有効性確認 (ソース[1])
        try:
            # 指定されたトークンで一時的なAPIクライアントを作成し、
            # ボット情報を取得できるか試すことで有効性を確認する
            temp_api = LineBotApi(token)
            temp_api.get_bot_info()
            return True
=======
    def __init__(self):
        # LINE Notifier の初期化
        self.line_token = os.getenv("LINE_TOKEN")
        if not self.line_token:
            raise ValueError("エラー: LINE_TOKENが設定されていません。")

    def validateLineToken(self, token):
        # LINE API トークンの有効性確認
        url = "https://api.line.me/v2/bot/profile"
        headers = {
            "Authorization": f"Bearer {token}"
        }
        
        try:
            response = requests.get(url, headers=headers)
            return response.status_code == 200
>>>>>>> main
        except Exception as e:
            print(f"トークン検証エラー: {e}")
            return False

<<<<<<< HEAD
def sendLineNotification(self, message):
        # LINE Messaging APIを呼び出し、家族へ通知する (ソース[1])
        # トークンやユーザーIDが未設定の場合はエラーを返す
        if not self.line_bot_api or not self.user_id:
            print("LINE_CHANNEL_ACCESS_TOKEN または LINE_USER_ID が未設定です。")
            return False

        try:
            # 指定したユーザーIDにメッセージを送信する (ソース[5])
            self.line_bot_api.push_message(
                self.user_id,
                TextSendMessage(text=message)
            )
            return True # 送信成功
        except Exception as e:
            print(f"LINE送信エラー: {e}")
            return False # 送信失敗 LINE Messaging APIを呼び出し、家族へ通知する
        pass
=======
    def sendLineNotification(self, message, user_id=None):
        """
        LINE Messaging APIを呼び出し、家族へ通知する
        
        Args:
            message (str): 送信するメッセージ内容
            user_id (str, optional): 送信先ユーザーID。未指定の場合は環境変数から取得
            
        Returns:
            bool: 送信成功時 True、失敗時 False
        """
        # 宛先IDが指定されていない場合は、環境変数から取得
        if user_id is None:
            user_id = os.getenv("LINE_USER_ID")

        if not self.line_token or not user_id:
            print("エラー: LINEトークンまたは宛先IDが設定されていません。")
            return False

        # LINE Messaging API のプッシュ通知用エンドポイント
        url = "https://api.line.me/v2/bot/message/push"

        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {self.line_token}"
        }

        # 送信するデータ（特定の個人に送るための 'to' を指定）
        data = {
            "to": user_id,
            "messages": [
                {
                    "type": "text",
                    "text": message
                }
            ]
        }

        try:
            response = requests.post(url, headers=headers, json=data)
            
            # 成功したら 200 が返ってくる
            if response.status_code == 200:
                print(f"通知送信成功: {message}")
                return True
            else:
                print(f"通知送信失敗 (ステータスコード: {response.status_code})")
                print(f"レスポンス詳細: {response.text}")
                return False

        except Exception as e:
            print(f"通信エラーが発生しました: {e}")
            return False

    def sendUrgentAlert(self, message, priority, user_id=None):
        """
        緊急度の高い通知を送信
        
        Args:
            message (str): 送信するメッセージ内容
            priority (str): 優先度レベル ("high", "medium", "low")
            user_id (str, optional): 送信先ユーザーID
            
        Returns:
            bool: 送信成功時 True、失敗時 False
        """
        # 優先度に応じてメッセージをフォーマット
        priority_prefix = {
            "high": "🚨【緊急】",
            "medium": "⚠️【警告】",
            "low": "ℹ️【通知】"
        }
        
        formatted_message = f"{priority_prefix.get(priority, '【通知】')}{message}"
        return self.sendLineNotification(formatted_message, user_id)
>>>>>>> main
