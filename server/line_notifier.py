import os
import reqest

class LineNotifier:
    # 外部連携

    def validateLineToken(self, token):
        # LINE API トークンの有効性確認
        pass

    def sendLineNotification(message, user_id=None):
        # LINE Messaging APIを呼び出し、異常検知や生存確認を家族へ通知する
       　#指定された特定の個人（user_id）にプッシュ通知を送る関数
    #宛先IDが指定されていない場合は、テスト用に環境変数から取得する
    if user_id is None:
        user_id = os.getenv("LINE_USER_ID")

    if not LINE_TOKEN or not user_id:
        print("エラー: LINEトークンまたは宛先IDが設定されていません。")
        return False

    # LINE Messaging API のプッシュ通知用エンドポイント
    url = "https://api.line.me/v2/bot/message/push"

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_TOKEN}"
    }

    # 送信するデータ (特定の個人に送るための 'to' を指定)
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
        
    def sendUrgentAlert(self, message, priority):
        # 緊急度の高い通知を送信
        pass

   
