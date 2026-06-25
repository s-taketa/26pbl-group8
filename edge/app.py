import time
import sys
import io
import json
import math
import wave
import struct
import threading
import subprocess
import requests
import cv2
from flask import Flask, request, jsonify, Response
from keyword_listener import KeywordListener
from image_processor import ImageProcessor

# ===================== 設定 =====================
SERVER_URL    = "http://192.168.100.103:5000"
# 音声合成(VOICEVOX)はサーバー側へ移設したため、エッジから直接アクセスしない
FLASK_PORT    = 5002
HEARTBEAT_INTERVAL = 30
# 再生デバイス。`aplay -l` で確認したスピーカーを plughw 形式で指定する。
# 例: "plughw:1,0"。空文字ならデフォルトデバイスを使う。
# plughw を使うと24000Hz等のレート変換を自動でやってくれる（aplay error 524対策）。
APLAY_DEVICE  = "plughw:2,0"
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
        # サーバー起動の場合はウェイクワードを待ってから聞き取る
        threading.Thread(
            target=recognition_flow,
            kwargs={"wait_for_wake_word": True},
            daemon=True,
        ).start()
        return jsonify({"status": "ok", "message": "認識フローを開始しました"})

    elif action == "stop":
        print("[SYSTEM] サーバーからの停止命令を受信しました。")
        return jsonify({"status": "ok", "message": "停止命令を受け付けました"})

    else:
        return jsonify({"status": "error", "message": f"未知のaction: {action}"}), 400


# ==================== コア機能 ====================

def recognition_flow(wait_for_wake_word: bool = False):
    print("[FLOW] 認識フロー開始")

    # wake_word_loop からは既に検知済みで呼ばれるため、ここでは再検知しない
    # （以前はここで detectKeyword() を再度呼び、ウェイクワードを2回言う必要があった）
    if wait_for_wake_word:
        is_detected = listener.detectKeyword()
        if not is_detected:
            print("[FLOW] ウェイクワード検知失敗")
            return
        print("[FLOW] ウェイクワード検知！")

    # 検知の合図（「ピッ」）を鳴らしてから聞き取り開始
    play_detect_sound()

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

    send_and_play(image_bytes, command)

    print("[FLOW] 認識フロー完了\n")


def _iter_frames(resp):
    """ストリーム応答を 4バイト長(BE)+本体 のフレーム単位で順に取り出す"""
    buf = bytearray()
    need = None
    for chunk in resp.iter_content(chunk_size=8192):
        if not chunk:
            continue
        buf.extend(chunk)
        while True:
            if need is None:
                if len(buf) < 4:
                    break
                need = struct.unpack(">I", bytes(buf[:4]))[0]
                del buf[:4]
            if len(buf) < need:
                break
            payload = bytes(buf[:need])
            del buf[:need]
            need = None
            yield payload


def _play_wav_bytes(wav: bytes):
    """受け取ったWAVバイト列をスピーカーから再生する"""
    with open("/tmp/voice_output.wav", "wb") as f:
        f.write(wav)

    cmd = ["aplay"]
    if APLAY_DEVICE:
        cmd += ["-D", APLAY_DEVICE]
    cmd.append("/tmp/voice_output.wav")
    subprocess.run(cmd, check=True)


def _make_chime_wav(notes, sample_rate: int = 44100, volume: float = 0.5) -> bytes:
    """
    (周波数Hz, 長さ秒) のリストから「ピコン♪」的なチャイムWAVをその場生成する。
    外部ファイルに依存せず標準ライブラリだけで作る。クリックノイズ防止に
    各音の前後を短くフェードする。
    """
    frames = bytearray()
    fade = int(0.005 * sample_rate)  # 5msのフェード
    for freq, dur in notes:
        n = int(sample_rate * dur)
        for i in range(n):
            env = min(1.0, i / fade, (n - i) / fade)  # 台形エンベロープ
            val = int(volume * env * 32767 * math.sin(2 * math.pi * freq * i / sample_rate))
            frames.extend(struct.pack("<h", val))

    buf = io.BytesIO()
    with wave.open(buf, "wb") as w:
        w.setnchannels(1)
        w.setsampwidth(2)       # 16bit
        w.setframerate(sample_rate)
        w.writeframes(bytes(frames))
    return buf.getvalue()


def play_startup_sound():
    """起動完了を知らせる「ピコン♪」を鳴らす（上がり2音）"""
    try:
        chime = _make_chime_wav([(1175, 0.09), (1568, 0.13)])  # D6 → G6
        _play_wav_bytes(chime)
        print("[SYSTEM] 起動音を再生しました（ピコン♪）")
    except Exception as e:
        print(f"[WARN] 起動音の再生に失敗: {e}")


def play_detect_sound():
    """ウェイクワード検知の合図（短い「ピッ」一発）"""
    try:
        beep = _make_chime_wav([(2093, 0.09)])  # C7
        _play_wav_bytes(beep)
    except Exception as e:
        # マイクと同じUSBデバイスを掴んでいて鳴らせない場合もあるが、
        # フロー自体は止めないよう警告だけにする。
        print(f"[WARN] 検知音の再生に失敗: {e}")


def send_and_play(image_bytes: bytes, command: str):
    """
    画像とコマンドをサーバーへ送り、返ってくる「回答テキスト＋文ごとのWAV」を
    ストリームで受け取りながら、届いた文から順に再生する。
    （音声合成はサーバー側VOICEVOXが担当。エッジは再生のみ）
    """
    try:
        files = {"image": ("capture.jpg", image_bytes, "image/jpeg")}
        data  = {"command": command}

        print(f"[SEND] サーバーへ送信中... → {SERVER_URL}/api/recognition")
        resp = requests.post(
            f"{SERVER_URL}/api/recognition",
            files=files,
            data=data,
            timeout=60,
            stream=True,
        )
        resp.raise_for_status()

        first = True
        played = 0
        for payload in _iter_frames(resp):
            if first:
                # 1フレーム目はメタJSON
                meta = json.loads(payload.decode("utf-8"))
                print(f"[RECV] 回答: 「{meta.get('answer_text')}」 "
                      f"(緊急={meta.get('is_emergency')})")
                first = False
                continue
            # 2フレーム目以降は文ごとのWAV
            played += 1
            print(f"[VOICE] 第{played}文を再生 ({len(payload)} bytes)")
            _play_wav_bytes(payload)

        if played == 0:
            print("[FLOW] サーバーから音声なし")
        else:
            print("[VOICE] 音声再生完了")

    except requests.exceptions.ConnectionError:
        print(f"[ERROR] サーバーに接続できません: {SERVER_URL}")
    except requests.exceptions.Timeout:
        print("[ERROR] 送信タイムアウト")
    except requests.exceptions.HTTPError as e:
        print(f"[ERROR] HTTPエラー: {e}")
    except Exception as e:
        print(f"[ERROR] 送受信中に予期しないエラー: {e}")


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

    # 起動完了の合図（マイクループがデバイスを掴む前に鳴らす）
    play_startup_sound()

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