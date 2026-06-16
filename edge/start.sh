#!/bin/bash
# VOICEVOX起動
~/voicevox_engine/run --host 0.0.0.0 --port 50021 &
echo "[VOICEVOX] 起動中... 5秒待機"
sleep 5

# エッジアプリ起動
source /home/pbl8/edge/env/bin/activate
python3 /home/pbl8/edge/app.py
