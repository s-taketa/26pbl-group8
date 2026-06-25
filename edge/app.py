# edge/app.py
import time
import requests
import os

class EdgeApp:
    # エッジ側のメイン制御およびサーバーとの通信を担当

    def __init__(self, server_base=None):
        # サーバーのベースURLは環境変数または引数で設定
        self.server_base = server_base or os.getenv("SERVER_BASE", "http://localhost:5000")

    def listenToServerRequest(self):
        """サーバーからの実行命令（音声開始など）を常時待ち受ける
        実装案:
         - 短いポーリング間隔でサーバーのAPIをチェックする
         - もしくは WebSocket を張る（将来的な改良）
        """
        # TODO: 実実装。現状はスタブ。
        pass

    def initializeEdgeDevice(self):
        # エッジデバイスの初期化（カメラ、マイクの準備）
        # TODO: カメラ／マイクを初期化する処理をここに記述
        pass

    def heartbeatCheck(self):
        # サーバーとの通信が維持されているかを定期的に確認する
        try:
            resp = requests.get(f"{self.server_base}/api/heartbeat", timeout=3)
            if resp.status_code == 200:
                # 正常
                return True
            return False
        except Exception as e:
            # 接続失敗は False を返す
            print(f"[EdgeApp] heartbeat error: {e}")
            return False

    def sendDataToServer(self, logData, image_path=None):
        # AIの判定結果、回答テキスト、撮影画像をサーバーの中央DBへ送信する
        # logData: dict (例: {"command": "...", "ai_response": "...", "is_emergency": 0})
        url = f"{self.server_base}/api/recognition"
        files = {}
        data = {"command": logData.get("command", "")}
        if image_path:
            try:
                files["image"] = open(image_path, "rb")
            except Exception as e:
                print(f"[EdgeApp] 画像ファイルを開けません: {e}")
        try:
            resp = requests.post(url, data=data, files=files if files else None, timeout=10)
            if files:
                files["image"].close()
            if resp.status_code == 200:
                return resp.json()
            else:
                print(f"[EdgeApp] sendDataToServer failed: {resp.status_code} {resp.text}")
                return None
        except Exception as e:
            print(f"[EdgeApp] sendDataToServer exception: {e}")
            return None

    def playVoice(self, audio_path):
        """VOICEVOX等で生成された音声をスピーカーから再生する（ローカル再生）"""
        # 簡易実装: aplay コマンドを使う（Raspberry Pi 等）
        try:
            # プラットフォームに合わせて再生コマンドを調整してください
            os.system(f"aplay {audio_path} 2>/dev/null")
        except Exception as e:
            print(f"[EdgeApp] playVoice error: {e}")


if __name__ == "__main__":
    app = EdgeApp()
    print("[INFO] EdgeApp起動。サーバーからの命令を待機します...")

    # 本実装が完成するまでの暫定処理（コンテナを起動状態に保つ）
    while True:
        ok = app.heartbeatCheck()
        print(f"[INFO] heartbeat: {'ok' if ok else 'fail'}")
        time.sleep(5)