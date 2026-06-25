# server/ai_logic.py

import google.generativeai as genai
import os
import json
import time
from PIL import Image
from dotenv import load_dotenv

load_dotenv()

# --- モデル初期化 ---
GEMINI_API_KEY = os.getenv("GOOGLE_GEMINI_API_KEY")
genai.configure(api_key=GEMINI_API_KEY)

# --- System Instruction（AIのアイデンティティ定義） ---
SYSTEM_INSTRUCTION = """
あなたは視覚障がい者の生活を支援するAIアシスタントです。
利用者の「目」として、周囲の状況を簡潔・正確に言語化してください。

【重要なルール】
- 回答は必ず以下のJSON形式のみで返すこと。前置きや説明文は一切不要です。
- 薬の飲み忘れ・転倒の予兆・刃物の放置など、危険な状況を正確に判断してください。
- is_emergency が 1 の場合のみ、category と alert_message を詳細に記述してください。

【出力形式】
{
  "answer": "利用者への回答（音声読み上げ用）",
  "is_emergency": 0,
  "category": "",
  "alert_message": ""
}

【category の種類】
- "fall_risk"       : 転倒の予兆・転倒している
- "medication"      : 薬の飲み忘れ・誤薬の可能性
- "dangerous_object": 刃物など危険物の放置
- "other_emergency" : その他の緊急事態
"""

# --- 生成設定（軽量化・高速化） ---
# response_mime_type で必ずJSONを返させ、コードブロック除去パースを不要にする。
# max_output_tokens で冗長な出力を抑え、生成時間とパース負荷を削減する。
GENERATION_CONFIG = {
    "response_mime_type": "application/json",
    "max_output_tokens": 512,
    "temperature": 0.4,
}

# --- モデルのインスタンス化 ---
# さらに高速化したい場合は "gemini-2.5-flash-lite" に切替（精度とのトレードオフ）。
model = genai.GenerativeModel(
    model_name="gemini-2.5-flash",
    system_instruction=SYSTEM_INSTRUCTION,
    generation_config=GENERATION_CONFIG,
)


def retryRequest(func, max_retries: int = 3, delay: float = 2.0):
    """
    共通の再試行ロジック
    APIタイムアウトやネットワーク遅延に対応する
    """
    last_error = None
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            last_error = e
            print(f"[WARN] 試行 {attempt + 1}/{max_retries} 失敗: {e}")
            if attempt < max_retries - 1:
                time.sleep(delay)
    raise RuntimeError(f"[ERROR] {max_retries}回試行しましたが失敗しました: {last_error}")


def processResponse(image: Image.Image, text: str) -> dict:
    """
    Gemini APIに画像とテキストを送信し、構造化JSONを返す

    Args:
        image : エッジ側でRGB補正（R-B入れ替え）済みのPIL Image
        text  : voice_handler.py でテキスト化された利用者の問いかけ

    Returns:
        dict: {"answer": str, "is_emergency": int, "category": str, "alert_message": str}
    """

    def _call_api():
        response = model.generate_content([image, text])
        raw = response.text.strip()

        # コードブロックが含まれる場合の除去
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]

        return json.loads(raw)

    result = retryRequest(_call_api)
    return result


# --- 単体テスト用エントリポイント ---
if __name__ == "__main__":
    import sys

    # テスト画像のパスを引数で受け取る（省略時はサンプル）
    image_path = sys.argv[1] if len(sys.argv) > 1 else "test_images/sample.jpg"
    test_text  = sys.argv[2] if len(sys.argv) > 2 else "今の周りの状況を教えてください"

    print(f"[TEST] 画像: {image_path}")
    print(f"[TEST] 質問: {test_text}")
    print("-" * 40)

    img = Image.open(image_path)
    result = processResponse(img, test_text)

    print(json.dumps(result, ensure_ascii=False, indent=2))

    # 緊急判定の確認
    if result.get("is_emergency") == 1:
        print(f"\n🚨 緊急検知: [{result.get('category')}] {result.get('alert_message')}")
    else:
        print("\n✅ 正常系: 緊急事態なし")