class VoiceHandler:
    # 音声認識と音声合成を扱うサーバーサイドのユーティリティクラス

    def convertSpeechToText(self, audioData):
        # Whisper 等を用いて、受け取った音声データをテキストに変換する。
        pass

    def playVoice(self, text):
        # VOICEVOX を使用し、回答テキストを音声データ（キャラクターボイス）に変換する。
        pass

    def removeNoise(self, audioData):
        # 音声認識の精度向上のため、背景ノイズを抑制する。
        pass
