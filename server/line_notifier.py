import os
import reqest

class LineNotifier:
    # 外部連携

    def validateLineToken(self, token):
        # LINE API トークンの有効性確認
        pass

    def sendLineNotification(self, message):
        # LINE Messaging APIを呼び出し、異常検知や生存確認を家族へ通知する
        """
    LINE Messaging APIを使用して家族へ通知を送る
    """
        # 2. 鍵がない場合のチェック
        if not LINE_CHANNEL_ACCESS_TOKEN:
            print("Error: LINE_CHANNEL_ACCESS_TOKEN is not set.")
            return False

        # 3. 送信先とヘッダーの設定
        url = "https://api.line.me/v2/bot/message/broadcast"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
        }
        
        # 4. 送信データ（引数の message を使う）
        payload = {
            "messages": [
                {
                    "type": "text",
                    "text": message
                }
            ]
        }

        try:
            # 5. 実行処理
            response = requests.post(url, headers=headers, json=payload)
            # return は必ずこの def (関数) の中に入れる
            return response.status_code == 200
        except Exception as e:
            print(f"LINE送信失敗: {e}")
            return False
            pass

    def sendUrgentAlert(self, message, priority):
        # 緊急度の高い通知を送信
        pass
        pass

   
