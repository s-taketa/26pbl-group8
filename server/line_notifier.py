class LineNotifier:
    # 外部連携

    def validateLineToken(self, token):
        # LINE API トークンの有効性確認
        pass

    def sendLineNotification(self, message):
        # LINE Messaging APIを呼び出し、異常検知や生存確認を家族へ通知する
    """
    LINE Messaging APIを使用して家族へ通知を送る
    引数: message (送信したい文章)
    戻り値: bool (成功ならTrue, 失敗ならFalse)
    """
    # トークンがない場合はエラー
    if not LINE_CHANNEL_ACCESS_TOKEN:
        return False

    # LINE APIの宛先（全員に送る「ブロードキャスト」の例）
    url = "https://api.line.me/v2/bot/message/broadcast"
    
    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {LINE_CHANNEL_ACCESS_TOKEN}"
    }
    
    # 送るデータの内容
    payload = {
        "messages": [
            {
                "type": "text",
                "text": message
            }
        ]
    }

    try:
        # 実際にLINEのサーバーへリクエストを送信
        response = requests.post(url, headers=headers, json=payload)
        # ステータスコードが200（成功）かどうかを返す
        return response.status_code == 200
    except Exception as e:
        print(f"LINE送信失敗: {e}")
        return False
        pass

    def sendUrgentAlert(self, message, priority):
        # 緊急度の高い通知を送信

        pass
