import os
import sys
import json
import time
import audioop
import pyaudio
from vosk import Model, KaldiRecognizer

class KeywordListener:
    def __init__(self, model_path: str = "model", sample_rate: int = 16000, chunk_size: int = 4000):
        self.model_path = model_path
        self.sample_rate = sample_rate
        self.chunk_size = chunk_size
        self.keywords = ["おにいちゃん", "起動して"]
        
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

    # 無音/過大入力の判定しきい値（16bit PCMのRMS）
    LOWER_THRESHOLD = 50
    UPPER_THRESHOLD = 30000

    def _rms(self, audioData: bytes) -> float:
        """16bit PCMのRMSをC実装(audioop)で高速計算する"""
        if not audioData:
            return 0.0
        try:
            return audioop.rms(audioData, 2)  # 2 = 16bit(2バイト)
        except audioop.error:
            return 0.0

    def removeNoise(self, audioData: bytes) -> bytes:
        # 旧実装は4000サンプルを純Pythonで毎チャンク二乗和しており、
        # 常時監視中ずっとCPUを消費していた。audioop.rms に置き換え。
        rms = self._rms(audioData)
        if rms < self.LOWER_THRESHOLD or rms > self.UPPER_THRESHOLD:
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

    # 発話とみなすRMSしきい値（これ未満は無音扱い）
    VOICE_THRESHOLD = 150

    def listen_command(self, timeout: int = 5, silence_limit: float = 0.8) -> str:
        """
        ウェイクワード検知後、マイクを開いたまま続けてユーザーの命令を聞き取ります。
        いったん発話を検知した後に silence_limit 秒の無音が続けば即終了します。
        （旧実装は無音チャンクをVoskに渡さず終端検知が働かないため、ほぼ毎回
          timeout いっぱい待っていた。RMSベースの無音判定で早期に打ち切る）
        """
        print("\n🗣️ 「ピロッ♪」 （ご用件をどうぞ！最大5秒待機します）")
        start_time = time.time()
        last_voice_time = None  # 最後に「声」を検知した時刻

        try:
            while time.time() - start_time < timeout:
                data = self.audio_stream.read(self.chunk_size, exception_on_overflow=False)
                clean_data = self.removeNoise(data)

                if clean_data is not None:
                    # 発話中かどうかを判定（しきい値以上のときだけ更新）
                    if self._rms(clean_data) >= self.VOICE_THRESHOLD:
                        last_voice_time = time.time()

                    # AcceptWaveform は話し終わり（沈黙）の瞬間に True になります
                    if self.recognizer.AcceptWaveform(clean_data):
                        result = json.loads(self.recognizer.Result())
                        text = result.get("text", "").replace(" ", "")
                        if text:
                            return text

                # いったん喋ってから一定時間無音が続いたら打ち切る
                if last_voice_time is not None and (time.time() - last_voice_time) > silence_limit:
                    break

            # 途中まで話していた内容を取り出す
            result = json.loads(self.recognizer.FinalResult())
            return result.get("text", "").replace(" ", "")

        except Exception as e:
            print(f"[ERROR] 命令の取得中にエラーが発生しました: {e}")
            return ""