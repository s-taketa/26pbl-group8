import cv2
from picamera2 import Picamera2

class ImageProcessor:
    def __init__(self):
        print("[INFO] カメラモジュール（目）を初期化・ウォームアップ中...")
        self.picam = Picamera2()
        
        # BGR888で取得
        config = self.picam.create_video_configuration(
            main={"format": "BGR888", "size": (640, 480)}
        )
        self.picam.configure(config)
        self.picam.start()
        print("[INFO] カメラの待機状態OK！いつでも撮影できるよ。")

    def capture_for_server(self) -> bytes:
        frame = self.picam.capture_array()

        # 【力技】RとBを強制スワップ
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

        success, buffer = cv2.imencode('.jpg', frame)
        if not success:
            print("[ERROR] 画像のJPEGエンコードに失敗しました。")
            return None

        return buffer.tobytes()

    def get_camera_info(self) -> dict:
        try:
            metadata = self.picam.capture_metadata()
            return {
                "露出時間(μs)":   metadata.get("ExposureTime", "N/A"),
                "アナログゲイン": round(metadata.get("AnalogueGain", 0), 2),
                "色温度(K)":      metadata.get("ColourTemperature", "N/A"),
                "輝度":           round(metadata.get("Lux", 0), 1),
            }
        except Exception as e:
            print(f"[WARN] カメラ情報の取得に失敗: {e}")
            return {}

    def close(self):
        self.picam.stop()
        print("[INFO] カメラモジュールを安全に終了しました。")
