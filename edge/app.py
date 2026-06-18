import time
import sys
import threading
import requests
import cv2
from flask import Flask, request, jsonify, Response
from keyword_listener import KeywordListener
from image_processor import ImageProcessor

# ===================== 設定 =====================
SERVER_URL    = "http://192.168.100.103:5000"
VOICEVOX_URL  = "http://localhost:50021"
FLASK_PORT    = 5002
HEARTBEAT_INTERVAL = 30
# ================================================

app_flask = Flask(__name__)

listener: KeywordListener = None
eye: ImageProcessor       = None

# ==================== リアルタイム映像配信 ====================

def generate_video_stream():
    """カメラ映像をMJPEGストリームとして配信する"""
    while True:
        frame = eye.picam.capture_array()
        bgr_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        # カメラ情報を描画
        metadata = eye.picam.capture_metadata()
        lines = [
            f"Exposure: {metadata.get('ExposureTime', 'N/A')} us",
            f"Gain:     {round(metadata.get('AnalogueGain', 0), 2)}",
            f"Temp:     {metadata.get('ColourTemperature', 'N/A')} K",
            f"Lux:      {round(metadata.get('Lux', 0), 1)}",
        ]
        for i, line in enumerate(lines):
            cv2.putText(bgr_frame, line, (10, 30 + i * 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        success, buffer = cv2.imencode('.jpg', bgr_frame)
        if not success:
            continue

        frame_bytes = buffer.tobytes()
        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')


@app_flask.route('/video')
def video():
    """ブラウザで開くとリアルタイム映像が見られる"""
    return Response(generate_video_stream(),
                     mimetype='multipart/x-mixed-replace; boundary=frame')


@app_flask.route('/')
def index():
    return '<html><body><h2>Camera Live View</h2><img src="/video"></body></html>'


# ==================== サーバーからの命令受付 ====================

@app_flask.route('/command', methods=['POST'])
def listen_to_server_request():
    data = request.get_json()
    if not data or "action" not in data:
        return jsonify({"status": "error", "message": "actionが指定されていません"}), 400

    action = data["action"]
    print(f"[SERVER→EDGE] 命令受信: {action}")

    if action == "start_recognition":
        threading.Thread(target=recognition_flow, daemon=True).start()
        return jsonify({"status": "ok", "message": "認識フローを開始しました"})

    elif action == "stop":
        print("[SYSTEM] サーバーからの停止命令を受信しました。")
        return jsonify({"status": "ok", "message": "停止命令を受け付けました"})

    else:
        return jsonify({"status": "error", "message": f"未知のaction: {action}"}), 400


# ==================== コア機能 ====================

def recognition_flow():
    print("[FLOW] 認識フロー開始")

    is_detected = listener.detectKeyword()
    if not is_detected:
        print("[FLOW] ウェイクワード検知失敗")
        return

    print("[FLOW] ウェイクワード検知！")

    command = listener.listen_command(timeout=5)
    listener.stopListening()

    if not command:
        print("[FLOW] コマンド聞き取り失敗")
        return

    print(f"[FLOW] コマンド取得: 「{command}」")

    print("[CAMERA] ===== 撮影時カメラ情報 =====")
    for k, v in eye.get_camera_info().items():
        print(f"[CAMERA]   {k}: {v}")
    print("[CAMERA] ================================")

    image_bytes = eye.capture_for_server()
    if not image_bytes:
        print("[FLOW] 画像取得失敗")
        return

    print(f"[FLOW] 画像取得完了 ({len(image_bytes)} bytes)")

    response_text = send_data_to_server(image_bytes, command)

    if response_text:
        play_voice(response_text)
    else:
        print("[FLOW] サーバーから回答テキストなし")

    print("[FLOW] 認識フロー完了\n")


def send_data_to_server(image_bytes: bytes, command: str) -> str:
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
    try:
        print(f"[VOICE] 音声生成中: 「{text}」")

        query_resp = requests.post(
            f"{VOICEVOX_URL}/audio_query",
            params={"text": text, "speaker": 1},
            timeout=10
        )
        query_resp.raise_for_status()
        query = query_resp.json()

        synth_resp = requests.post(
            f"{VOICEVOX_URL}/synthesis",
            params={"speaker": 1},
            json=query,
            timeout=15
        )
        synth_resp.raise_for_status()

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

    try:
        print("[SYSTEM] 音声モジュール（耳）を初期化中...")
        listener = KeywordListener(model_path="model")

        print("[SYSTEM] カメラモジュール（目）を初期化中...")
        eye = ImageProcessor()

    except Exception as e:
        print(f"[FATAL] 初期化失敗: {e}")
        sys.exit(1)

    print("\n[CAMERA] ===== 起動時カメラ情報 =====")
    for k, v in eye.get_camera_info().items():
        print(f"[CAMERA]   {k}: {v}")
    print("[CAMERA] ================================\n")

    threading.Thread(target=heartbeat_check, daemon=True).start()
    print(f"[SYSTEM] ハートビート監視開始（{HEARTBEAT_INTERVAL}秒間隔）")

    threading.Thread(target=wake_word_loop, daemon=True).start()
    print("[SYSTEM] ウェイクワード待機ループ開始")

    print(f"[SYSTEM] Flaskサーバー起動 → ポート {FLASK_PORT}")
    print("="*55)
    print(f"  サーバーからの命令受付: POST http://<RasPiIP>:{FLASK_PORT}/command")
    print(f"  リアルタイム映像確認  : GET  http://<RasPiIP>:{FLASK_PORT}/video")
    print(f"  終了: Ctrl + C")
    print("="*55 + "\n")
    app_flask.run(host='0.0.0.0', port=FLASK_PORT, threaded=True)


def wake_word_loop():
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