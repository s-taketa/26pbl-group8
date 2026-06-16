class EdgeApp:
    # エッジ側のメイン制御およびサーバーとの通信を担当

    def initializeEdgeDevice(self):
        # エッジデバイスの初期化（カメラ、マイクの準備）
        pass

    def heartbeatCheck(self):
        # サーバーとの通信が維持されているかを定期的に確認する
        pass

    def listenToServerRequest(self):
        # サーバーからの実行命令（認識開始など）を常時待ち受ける
        pass

    def startRecognition(self):
        # サーバー命令に応じて認識を開始
        pass

    def stopRecognition(self):
        # 認識を停止
        pass

    def sendDataToServer(self, logData):
        # AIの判定結果、回答テキスト、撮影画像をサーバーの中央DBへ送信する
        pass

    def playVoice(self, audio):
        # VOICEVOX等で生成された音声をスピーカーから再生する
        pass