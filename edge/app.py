import time
import sys
import threading
import requests
from flask import Flask, request, jsonify
from keyword_listener import KeywordListener
from image_processor import ImageProcessor

# ===================== 設定 =====================
SERVER_URL    = "http://192.168.100.103:5000"   # ← UbuntuサーバーのIPに変更
VOICEVOX_URL  = "http://localhost:50021"     # VOICEVOXはラズパイローカルで動作
FLASK_PORT    = 5002                          # ラズパイ側Flaskのポート
HEARTBEAT_INTERVAL = 30                       # ハートビート間隔（秒）
# ================================================

app_flask = Flask(__name__)

# モジュールをグローバルで保持（Flaskスレッドと共有）
listener: KeywordListener = None
eye: ImageProcessor       = None

# ==================== Flask エンドポイント ====================

@app_flask.route('/command', methods=['POST'])
def listen_to_server_request():
    """
    listenToServerRequest()
    サーバーからの実行命令を待ち受けるエンドポイント。
    受信例: {"action": "start_recognition"} / {"action": "stop"}
    """
    data = request.get_json()
    if not data or "action" not in data:
        return jsonify({"status": "error", "message": "actionが指定されていません"}), 400

    action = data["action"]
    print(f"[SERVER→EDGE] 命令受信: {action}")

    if action == "start_recognition":
        # 別スレッドで認識フローを起動（Flaskをブロックしないため）
        threading.Thread(target=recognition_flow, daemon=True).start()
        return jsonify({"status": "ok", "message": "認識フローを開始しました"})

    elif action == "stop":
        print("[SYSTEM] サーバーからの停止命令を受信しました。")
        return jsonify({"status": "ok", "message": "停止命令を受け付けました"})

    else:
        return jsonify({"status": "error", "message": f"未知のaction: {action}"}), 400


# ==================== コア機能 ====================

def recognition_flow():
    """
    ウェイクワード検知 → 命令取得 → 撮影 → サーバー送信 の一連フロー
    """
    print("[FLOW] 認識フロー開始")

    # 1. ウェイクワード待機
    is_detected = listener.detectKeyword()
    if not is_detected:
        print("[FLOW] ウェイクワード検知失敗")
        return

    print("[FLOW] ウェイクワード検知！")

    # 2. コマンド取得
    command = listener.listen_command(timeout=5)
    listener.stopListening()

    if not command:
        print("[FLOW] コマンド聞き取り失敗")
        return

    print(f"[FLOW] コマンド取得: 「{command}」")

    # 3. カメラ情報ログ
    print("[CAMERA] ===== 撮影時カメラ情報 =====")
    for k, v in eye.get_camera_info().items():
        print(f"[CAMERA]   {k}: {v}")
    print("[CAMERA] ================================")

    # 4. 画像撮影
    image_bytes = eye.capture_for_server()
    if not image_bytes:
        print("[FLOW] 画像取得失敗")
        return

    print(f"[FLOW] 画像取得完了 ({len(image_bytes)} bytes)")

    # 5. サーバーへ送信 → AIの回答テキストを受け取る
    response_text = send_data_to_server(image_bytes, command)

    # 6. 回答をボイスで再生
    if response_text:
        play_voice(response_text)
    else:
        print("[FLOW] サーバーから回答テキストなし")

    print("[FLOW] 認識フロー完了\n")


def send_data_to_server(image_bytes: bytes, command: str) -> str:
    """
    sendDataToServer()
    画像・コマンドをサーバーへ送信し、AIの回答テキストを返す。
    戻り値: 回答テキスト（失敗時はNone）
    """
    try:
        files = {"image": ("capture.jpg", image_bytes, "image/jpeg")}
        data  = {"command": command}

        print(f"[SEND] サーバーへ送信中... → {SERVER_URL}/api/recognition")
        resp = requests.post(
            f"{SERVER_URL}/api/recognition",
            files=files,
            data=data,
            timeout=15
        )
        resp.raise_for_status()

        result = resp.json()
        print(f"[RECV] サーバーレスポンス: {result}")
        return result.get("answer_text")

    except requests.exceptions.ConnectionError:
        print(f"[ERROR] サーバーに接続できません: {SERVER_URL}")
    except requests.exceptions.Timeout:
        print("[ERROR] 送信タイムアウト")
    except requests.exceptions.HTTPError as e:
        print(f"[ERROR] HTTPエラー: {e}")
    except Exception as e:
        print(f"[ERROR] 送信中に予期しないエラー: {e}")
    return None


def play_voice(text: str):
    """
    playVoice()
    VOICEVOXを使ってテキストをキャラクターボイスで再生する。
    """
    try:
        print(f"[VOICE] 音声生成中: 「{text}」")

        # Step1: 音声クエリ生成
        query_resp = requests.post(
            f"{VOICEVOX_URL}/audio_query",
            params={"text": text, "speaker": 1},
            timeout=10
        )
        query_resp.raise_for_status()
        query = query_resp.json()

        # Step2: 音声合成
        synth_resp = requests.post(
            f"{VOICEVOX_URL}/synthesis",
            params={"speaker": 1},
            json=query,
            timeout=15
        )
        synth_resp.raise_for_status()

        # Step3: WAVファイルとして保存して再生
        with open("/tmp/voice_output.wav", "wb") as f:
            f.write(synth_resp.content)

        import subprocess
        subprocess.run(["aplay", "/tmp/voice_output.wav"], check=True)
        print("[VOICE] 音声再生完了")

    except requests.exceptions.ConnectionError:
        print("[WARN] VOICEVOXに接続できません（起動しているか確認してください）")
    except Exception as e:
        print(f"[ERROR] 音声再生エラー: {e}")


def heartbeat_check():
    """
    heartbeatCheck()
    30秒ごとにサーバーへ死活確認を送り、接続状態をログに出す。
    """
    while True:
        try:
            resp = requests.get(f"{SERVER_URL}/api/heartbeat", timeout=5)
            if resp.status_code == 200:
                print(f"[HEARTBEAT] ✅ サーバー接続OK ({SERVER_URL})")
            else:
                print(f"[HEARTBEAT] ⚠️ サーバー応答異常: {resp.status_code}")
        except requests.exceptions.ConnectionError:
            print(f"[HEARTBEAT] ❌ サーバーに接続できません ({SERVER_URL})")
        except Exception as e:
            print(f"[HEARTBEAT] エラー: {e}")

        time.sleep(HEARTBEAT_INTERVAL)


# ==================== 起動処理 ====================

def main():
    global listener, eye

    print("[SYSTEM] エッジデバイスを起動します...")

    # モジュール初期化
    try:
        print("[SYSTEM] 音声モジュール（耳）を初期化中...")
        listener = KeywordListener(model_path="model")

        print("[SYSTEM] カメラモジュール（目）を初期化中...")
        eye = ImageProcessor()

    except Exception as e:
        print(f"[FATAL] 初期化失敗: {e}")
        sys.exit(1)

    # 起動時カメラ情報表示
    print("\n[CAMERA] ===== 起動時カメラ情報 =====")
    for k, v in eye.get_camera_info().items():
        print(f"[CAMERA]   {k}: {v}")
    print("[CAMERA] ================================\n")

    # ハートビートを別スレッドで起動
    threading.Thread(target=heartbeat_check, daemon=True).start()
    print(f"[SYSTEM] ハートビート監視開始（{HEARTBEAT_INTERVAL}秒間隔）")

    # ウェイクワード待機ループを別スレッドで起動
    threading.Thread(target=wake_word_loop, daemon=True).start()
    print("[SYSTEM] ウェイクワード待機ループ開始")

    # FlaskサーバーをメインスレッドでListen（サーバーからの命令受付）
    print(f"[SYSTEM] Flaskサーバー起動 → ポート {FLASK_PORT}")
    print("="*55)
    print(f"  サーバーからの命令受付: POST http://<RasPiIP>:{FLASK_PORT}/command")
    print(f"  終了: Ctrl + C")
    print("="*55 + "\n")
    app_flask.run(host='0.0.0.0', port=FLASK_PORT)


def wake_word_loop():
    """
    ウェイクワードを常時監視し、検知したら認識フローを起動するループ。
    サーバーからの /command とは独立して動作する。
    """
    print("[WAKE] ウェイクワード監視ループ開始")
    try:
        while True:
            is_detected = listener.detectKeyword()
            if is_detected:
                print("[WAKE] ウェイクワード検知 → 認識フロー起動")
                recognition_flow()
            time.sleep(0.1)
    except Exception as e:
        print(f"[WAKE] ループエラー: {e}")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n[SYSTEM] 終了します...")
    finally:
        if eye:
            eye.close()
        print("[SYSTEM] シャットダウン完了。")