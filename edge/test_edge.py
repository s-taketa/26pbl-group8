"""
エッジデバイス → サーバー 結合テストスクリプト
実行: python3 test_edge.py
"""

import time
import sys
import os
import requests
import json

# ===================== 設定 =====================
SERVER_URL   = "http://192.168.100.103:5000"   # ← 実際のIPに変更
VOICEVOX_URL = "http://localhost:50021"
SAVE_DIR     = "./test_outputs"
# ================================================

os.makedirs(SAVE_DIR, exist_ok=True)

# ========== ユーティリティ ==========

def print_header(title: str):
    print("\n" + "="*55)
    print(f"  テスト: {title}")
    print("="*55)

def print_result(success: bool, message: str):
    mark = "✅ PASS" if success else "❌ FAIL"
    print(f"  {mark} : {message}")

results = []

def record(name: str, success: bool, detail: str = ""):
    results.append({"name": name, "success": success, "detail": detail})
    print_result(success, f"{name} {('/ ' + detail) if detail else ''}")


# ========== テスト1: ウェイクワード後のコマンド取得 ==========

def test_keyword_and_command():
    print_header("ウェイクワード検知 + コマンド取得")

    try:
        from keyword_listener import KeywordListener
        listener = KeywordListener(model_path="model")
        print("  [INFO] マイクに向かって「チャピー」と呼びかけてください...")

        is_detected = listener.detectKeyword()
        if not is_detected:
            record("ウェイクワード検知", False, "検知されなかった")
            return None

        record("ウェイクワード検知", True)

        print("  [INFO] 続けてコマンドを話してください（例：「何が見える？」）")
        command = listener.listen_command(timeout=5)
        listener.stopListening()

        if command:
            record("コマンド取得", True, f"取得内容: 「{command}」")
            return command
        else:
            record("コマンド取得", False, "無音または認識失敗")
            return None

    except Exception as e:
        record("ウェイクワード/コマンドテスト", False, str(e))
        return None


# ========== テスト2: カメラ撮影 + 画像確認 ==========

def test_camera_capture():
    print_header("カメラ撮影・画像確認")

    try:
        from image_processor import ImageProcessor
        eye = ImageProcessor()

        # カメラ情報表示
        print("  [CAMERA INFO]")
        for k, v in eye.get_camera_info().items():
            print(f"    {k}: {v}")

        # 撮影
        image_bytes = eye.capture_for_server()
        eye.close()

        if not image_bytes:
            record("カメラ撮影", False, "image_bytesがNone")
            return None

        record("カメラ撮影", True, f"{len(image_bytes)} bytes")

        # ローカル保存して目視確認できるようにする
        save_path = f"{SAVE_DIR}/test_capture_{int(time.time())}.jpg"
        with open(save_path, "wb") as f:
            f.write(image_bytes)
        record("画像ローカル保存", True, f"→ {save_path} を開いて色ズレがないか確認してね")

        return image_bytes

    except Exception as e:
        record("カメラテスト", False, str(e))
        return None


# ========== テスト3: サーバー送信 ==========

def test_send_to_server(image_bytes: bytes, command: str):
    print_header("サーバーへのデータ送信")

    try:
        files = {"image": ("capture.jpg", image_bytes, "image/jpeg")}
        data  = {"command": command}

        print(f"  [SEND] → {SERVER_URL}/api/recognition")
        resp = requests.post(
            f"{SERVER_URL}/api/recognition",
            files=files,
            data=data,
            timeout=15
        )

        record("HTTP送信ステータス", resp.status_code == 200, f"status={resp.status_code}")

        result = resp.json()
        print(f"  [RECV] レスポンス内容: {json.dumps(result, ensure_ascii=False, indent=2)}")

        answer_text = result.get("answer_text")
        record("answer_textの受信", bool(answer_text), f"内容: 「{answer_text}」")

        return answer_text

    except requests.exceptions.ConnectionError:
        record("サーバー送信", False, f"接続できません: {SERVER_URL}")
    except requests.exceptions.Timeout:
        record("サーバー送信", False, "タイムアウト")
    except Exception as e:
        record("サーバー送信", False, str(e))
    return None


# ========== テスト4: VOICEVOX音声再生 ==========

def test_voicevox(text: str = "テスト再生です。聞こえていますか？"):
    print_header("VOICEVOX 音声再生")

    try:
        # Step1: audio_query
        q = requests.post(
            f"{VOICEVOX_URL}/audio_query",
            params={"text": text, "speaker": 1},
            timeout=10
        )
        record("audio_query", q.status_code == 200, f"status={q.status_code}")

        # Step2: synthesis
        s = requests.post(
            f"{VOICEVOX_URL}/synthesis",
            params={"speaker": 1},
            json=q.json(),
            timeout=15
        )
        record("synthesis", s.status_code == 200, f"status={s.status_code}")

        # Step3: 再生
        wav_path = "/tmp/test_voice.wav"
        with open(wav_path, "wb") as f:
            f.write(s.content)

        import subprocess
        ret = subprocess.run(["aplay", wav_path], capture_output=True)
        record("aplay再生", ret.returncode == 0,
               "成功" if ret.returncode == 0 else ret.stderr.decode())

    except requests.exceptions.ConnectionError:
        record("VOICEVOX接続", False, f"VOICEVOXが起動していません: {VOICEVOX_URL}")
    except Exception as e:
        record("VOICEVOXテスト", False, str(e))


# ========== テスト5: ハートビート ==========

def test_heartbeat():
    print_header("ハートビート（サーバー死活確認）")

    try:
        resp = requests.get(f"{SERVER_URL}/api/heartbeat", timeout=5)
        record("ハートビート応答", resp.status_code == 200,
               f"status={resp.status_code} / body={resp.text[:80]}")
    except requests.exceptions.ConnectionError:
        record("ハートビート", False, f"接続できません: {SERVER_URL}")
    except Exception as e:
        record("ハートビート", False, str(e))


# ========== テスト6: Flaskエンドポイント（ラズパイ側） ==========

def test_flask_endpoint():
    print_header("ラズパイFlask /command エンドポイント")

    try:
        resp = requests.post(
            "http://localhost:5002/command",
            json={"action": "start_recognition"},
            timeout=5
        )
        record("/command受付", resp.status_code == 200,
               f"レスポンス: {resp.json()}")
    except requests.exceptions.ConnectionError:
        record("/command", False, "app.pyが起動していません（ポート5002）")
    except Exception as e:
        record("/commandテスト", False, str(e))


# ========== メイン ==========

def main():
    print("\n" + "★"*55)
    print("  エッジデバイス 結合テスト開始")
    print("★"*55)

    # テスト1: ウェイクワード + コマンド
    command = test_keyword_and_command()
    if not command:
        command = "テスト用コマンド"  # 失敗しても後続テストを続ける

    # テスト2: カメラ撮影
    image_bytes = test_camera_capture()

    # テスト3: サーバー送信（画像・コマンドが揃っている場合のみ）
    answer_text = None
    if image_bytes:
        answer_text = test_send_to_server(image_bytes, command)
    else:
        print("\n[SKIP] 画像なし → サーバー送信テストをスキップ")

    # テスト4: VOICEVOX（サーバーから回答が来た場合はそれを再生）
    test_voicevox(answer_text or "テスト再生です。聞こえていますか？")

    # テスト5: ハートビート
    test_heartbeat()

    # テスト6: Flaskエンドポイント
    test_flask_endpoint()

    # ========== 結果サマリ ==========
    print("\n" + "="*55)
    print("  テスト結果サマリ")
    print("="*55)
    passed = sum(1 for r in results if r["success"])
    failed = sum(1 for r in results if not r["success"])
    for r in results:
        mark = "✅" if r["success"] else "❌"
        print(f"  {mark} {r['name']}")
        if r["detail"]:
            print(f"       → {r['detail']}")
    print("-"*55)
    print(f"  合計: {passed}件PASS / {failed}件FAIL")
    print("="*55 + "\n")

if __name__ == "__main__":
    main()