import os
from linebot import LineBotApi
from linebot.models import TextSendMessage

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

def validateLineToken(self, token):
        # LINE API トークンの有効性確認
        #LINE API トークンの有効性確認 (ソース[1])
        try:
            # 指定されたトークンで一時的なAPIクライアントを作成し、
            # ボット情報を取得できるか試すことで有効性を確認する
            temp_api = LineBotApi(token)
            temp_api.get_bot_info()
            return True
        except Exception as e:
            print(f"トークン検証エラー: {e}")
            return False

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