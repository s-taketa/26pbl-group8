# server/voice_handler.py
# 音声認識・音声合成を扱うサーバーサイドのユーティリティクラス。
# 音声合成(VOICEVOX)はエッジ(Pi)からサーバーへ移設した。Pi5は常時音声監視・
# カメラ処理でCPUが逼迫するため、合成をサーバーで行い高速化・負荷分散する。

import os
import re
import requests


class VoiceHandler:
    """音声認識と音声合成を扱うサーバーサイドのユーティリティクラス"""

    def __init__(self, host: str = None, port: str = None, speaker: int = None):
        # docker-compose ではサービス名 "voicevox" で解決できる。
        # サーバーで直接VOICEVOXを動かす場合は VOICEVOX_HOST=localhost を指定する。
        self.host = host or os.getenv("VOICEVOX_HOST", "voicevox")
        self.port = port or os.getenv("VOICEVOX_PORT", "50021")
        self.speaker = speaker if speaker is not None else int(os.getenv("VOICEVOX_SPEAKER", "1"))
        self.voicevox_url = f"http://{self.host}:{self.port}"

    # ==================== 音声認識（STT）: 未実装 ====================

    def convertSpeechToText(self, audioData):
        # Whisper 等を用いて、受け取った音声データをテキストに変換する。
        pass

    def removeNoise(self, audioData):
        # 音声認識の精度向上のため、背景ノイズを抑制する。
        pass

    # ==================== 音声合成（TTS / VOICEVOX） ====================

    def split_sentences(self, text: str):
        """句点・改行で文に分割する（空文字は除く）"""
        sentences = [s for s in re.split(r'(?<=[。！？\n])', text) if s.strip()]
        return sentences or ([text] if text.strip() else [])

    def synthesize(self, sentence: str, speaker: int = None, timeout: float = 20.0) -> bytes:
        """1文をVOICEVOXで合成し、WAVバイト列を返す"""
        speaker = self.speaker if speaker is None else speaker

        query_resp = requests.post(
            f"{self.voicevox_url}/audio_query",
            params={"text": sentence, "speaker": speaker},
            timeout=timeout,
        )
        query_resp.raise_for_status()

        synth_resp = requests.post(
            f"{self.voicevox_url}/synthesis",
            params={"speaker": speaker},
            json=query_resp.json(),
            timeout=timeout,
        )
        synth_resp.raise_for_status()
        return synth_resp.content

    def synthesize_stream(self, text: str, speaker: int = None):
        """
        テキストを文単位で順次合成し、合成できた文からWAVバイト列を yield する。
        1文の合成に失敗しても全体は止めず、その文だけスキップする。
        """
        for sentence in self.split_sentences(text):
            try:
                yield self.synthesize(sentence, speaker)
            except Exception as e:
                print(f"[TTS] 合成失敗（スキップ）: {sentence!r}: {e}")
                continue