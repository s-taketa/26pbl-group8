　# edge/app.py
import time

class EdgeApp:
    """エッジ側のメイン制御およびサーバーとの通信を担当"""

    def listenToServerRequest(self):
        """サーバーからの実行命令（音声開始など）を常時待ち受ける"""
        # TODO: 実装: サーバーAPIをポーリング、またはWebSocketで待機する
        pass

    def initializeEdgeDevice(self):
        """エッジデバイスの初期化（カメラ、マイクの準備）"""
        # TODO: カメラやマイクの初期化処理を追加
        pass

    def heartbeatCheck(self):
        """サーバーとの通信が維持されているかを定期的に確認する"""
        # TODO: サーバーの /api/heartbeat に GET を投げて死活監視
        pass

    def sendDataToServer(self, logData):
        """AIの判定結果、回答テキスト、撮影画像をサーバーの中央DBへ送信する"""
        # TODO: multipart/form-data で /api/recognition 等へ送信する処理
        pass

    def playVoice(self, audio):
        """VOICEVOX等で生成された音声をスピーカーから再生する"""
        # TODO: 音声ファイルの再生処理（aplay など）を実装
        pass


if __name__ == "__main__":
    app = EdgeApp()
    print("[INFO] EdgeApp起動。サーバーからの命令を待機します...")

    # 本実装が完成するまでの暫定処理（コンテナを起動状態に保つ）
    while True:
        app.heartbeatCheck()
        time.sleep(5)