import os
import sys
import json
import time
import pyaudio
import math
import array
from vosk import Model, KaldiRecognizer

class KeywordListener:
    def __init__(self, model_path: str = "model", sample_rate: int = 16000, chunk_size: int = 4000):
        self.model_path = model_path
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.keywords = ["チャピー", "起動して"]
        
        self.audio_interface = None
        self.audio_stream = None
        self.model = None
        self.recognizer = None

        self._initialize_model()

    def _initialize_model(self) -> None:
        print("[INFO] 音声認識モデルを初期化しています...")
        if not os.path.exists(self.model_path):
            print(f"[ERROR] モデルディレクトリ '{self.model_path}' が見つかりません。")
            sys.exit(1)
            
        from vosk import SetLogLevel
        SetLogLevel(-1)
        
        self.model = Model(self.model_path)
        self.recognizer = KaldiRecognizer(self.model, self.sample_rate)
        print("[INFO] モデルの初期化が完了しました。")

    def startListening(self) -> None:
        """マイク入力を開始します。すでに開いている場合はスキップします。"""
        if self.audio_interface is None:
            self.audio_interface = pyaudio.PyAudio()

        # すでにマイクストリームがアクティブなら何もしない（シームレスに聞き続けるため）
        if self.audio_stream is not None and self.audio_stream.is_active():
            return

        rates_to_try = [16000, 48000, 44100, 8000]

        while True:
            for rate in rates_to_try:
                try:
                    self.audio_stream = self.audio_interface.open(
                        format=pyaudio.paInt16,
                        channels=1,
                        rate=rate,
                        input=True,
                        frames_per_buffer=self.chunk_size
                    )
                    print(f"[INFO] マイクのセットアップ完了！(サンプリングレート: {rate}Hz)")
                    
                    if self.sample_rate != rate:
                        self.sample_rate = rate
                        self.recognizer = KaldiRecognizer(self.model, self.sample_rate)
                        print(f"[INFO] 音声認識モデルを {rate}Hz 用に最適化しました。")
                    return

                except OSError:
                    continue

            print("[WARNING] マイクの初期化に失敗しました。3秒後に再試行します...")
            time.sleep(3)

    def stopListening(self) -> None:
        """マイクを一時的に解放します（カメラ撮影やAI音声再生とのリソース競合を防ぐため）"""
        if self.audio_stream is not None:
            self.audio_stream.stop_stream()
            self.audio_stream.close()
            self.audio_stream = None
            print("[INFO] マイクを一時的にミュート（解放）しました。")

    def removeNoise(self, audioData: bytes) -> bytes:
        try:
            samples = array.array('h', audioData)
        except ValueError:
            return None
            
        if not samples:
            return None
            
        sum_squares = sum(s * s for s in samples)
        rms = math.sqrt(sum_squares / len(samples))
        
        LOWER_THRESHOLD = 50
        UPPER_THRESHOLD = 30000

        if rms < LOWER_THRESHOLD or rms > UPPER_THRESHOLD:
            return None
            
        return audioData

    def detectKeyword(self) -> bool:
        self.startListening()
        print(f"\n[INFO] ウェイクワードの監視を開始しました: {self.keywords}")

        try:
            while True:
                try:
                    data = self.audio_stream.read(self.chunk_size, exception_on_overflow=False)
                except IOError:
                    time.sleep(0.5)
                    continue

                clean_data = self.removeNoise(data)
                if clean_data is None:
                    continue

                if self.recognizer.AcceptWaveform(clean_data):
                    result = json.loads(self.recognizer.Result())
                    text = result.get("text", "").replace(" ", "")

                    if not text:
                        continue

                    for keyword in self.keywords:
                        if keyword in text:
                            print(f"\n[EVENT] ウェイクワード '{keyword}' を検知しました！")
                            # 検知成功時はマイクを「開いたまま」Trueを返す
                            return True

        except KeyboardInterrupt:
            print("\n[INFO] プログラムの実行をユーザー操作により中断します。")
            self.stopListening()
            if self.audio_interface is not None:
                self.audio_interface.terminate()
                self.audio_interface = None
            return False

    def listen_command(self, timeout: int = 5) -> str:
        """
        ウェイクワード検知後、マイクを開いたまま続けてユーザーの命令を聞き取ります。
        沈黙（話し終わり）を検知するか、タイムアウトするとテキストを返します。
        """
        print("\n🗣️ 「ピロッ♪」 （ご用件をどうぞ！最大5秒待機します）")
        start_time = time.time()
        
        try:
            while time.time() - start_time < timeout:
                data = self.audio_stream.read(self.chunk_size, exception_on_overflow=False)
                clean_data = self.removeNoise(data)
                if clean_data is None:
                    continue
                    
                # AcceptWaveform はユーザーが「話し終わった（沈黙した）」瞬間に True になります
                if self.recognizer.AcceptWaveform(clean_data):
                    result = json.loads(self.recognizer.Result())
                    text = result.get("text", "").replace(" ", "")
                    if text:
                        return text
                        
            # タイムアウトした場合、途中まで話していた内容を取り出す
            result = json.loads(self.recognizer.FinalResult())
            return result.get("text", "").replace(" ", "")
            
        except Exception as e:
            print(f"[ERROR] 命令の取得中にエラーが発生しました: {e}")
            return ""