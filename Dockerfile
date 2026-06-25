# Dockerfile for AI見守りアシスタント
# Raspberry Pi 5（arm64）対応の Python 3.11 ベース環境

FROM python:3.11-slim

WORKDIR /app

# システムパッケージの更新とインストール
RUN apt-get update && apt-get install -y --no-install-recommends \
    # OpenCV 関連の依存ライブラリ
    libgl1 \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    # 音声処理関連
    portaudio19-dev \
    libportaudio2 \
    # その他必要なツール
    gcc \
    g++ \
    git \
    curl \
    # クリーンアップ
    && rm -rf /var/lib/apt/lists/*

# Python 依存ライブラリのインストール
# requirements.txt をコピーしてインストール
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# アプリケーションコードをコピー
COPY . .

# 環境変数の設定（デフォルト値）
# 本番運用時は docker-compose.yml または .env ファイルで上書きされます
ENV FLASK_APP=app.py \
    FLASK_ENV=production \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# ログと画像出力ディレクトリを作成
RUN mkdir -p /app/logs /app/images /app/audio

# ヘルスチェック（オプション：コンテナの状態監視用）
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# アプリケーションの起動
# Flask の場合: python app.py
# FastAPI の場合: uvicorn app:app --host 0.0.0.0 --port 8000
CMD ["python", "server/main.py"]