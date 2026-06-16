class EdgeApp:
    # エッジ側のメイン制御およびサーバーとの通信を担当
    
    def listenToServerRequest(self):
        # サーバーからの実行命令（認識開始など）を常時待ち受ける
        pass
    
    def sendDataToServer(self, logData):
        # AIの判定結果、回答テキスト、撮影画像をサーバーの中央DBへ送信する
        pass

    def playVoice(self, audio):
        # VOICEVOX等で生成された音声をスピーカーから再生する
        pass

    def heartbeatCheck(self):
        # サーバーとの通信が維持されているかを定期的に確認する
        pass