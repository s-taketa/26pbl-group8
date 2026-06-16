from flask import Flask, Response
from image_processor import ImageProcessor
import cv2

app = Flask(__name__)
eye = ImageProcessor()

def generate():
    while True:
        frame = eye.picam.capture_array()
        bgr = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)

        # カメラ情報をフレームに描画
        metadata = eye.picam.capture_metadata()
        lines = [
            f"Exposure: {metadata.get('ExposureTime', 'N/A')} us",
            f"Gain:     {round(metadata.get('AnalogueGain', 0), 2)}",
            f"Temp:     {metadata.get('ColourTemperature', 'N/A')} K",
            f"Lux:      {round(metadata.get('Lux', 0), 1)}",
        ]
        for i, line in enumerate(lines):
            cv2.putText(bgr, line, (10, 30 + i * 30),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)

        _, buffer = cv2.imencode('.jpg', bgr)
        frame_bytes = buffer.tobytes()

        yield (b'--frame\r\n'
               b'Content-Type: image/jpeg\r\n\r\n' + frame_bytes + b'\r\n')

@app.route('/video')
def video():
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/')
def index():
    return '<html><body><h2>Camera Preview</h2><img src="/video"></body></html>'

if __name__ == '__main__':
    print("ブラウザで開いてね → http://<RasPiのIP>:5001")
    app.run(host='0.0.0.0', port=5001)