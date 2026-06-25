#!/bin/bash

echo "[SYSTEM] VOICEVOXエンジンをバックグラウンドで起動します..."
~/voicevox_engine/run --host 0.0.0.0 --port 50021 &

# VOICEVOXが正常に立ち上がるまで2秒ごとに生存確認（賢い待機ループ）
echo "[SYSTEM] VOICEVOXの準備完了を待っています..."
until curl -s http://127.0.0.1:50021/version > /dev/null; do
    sleep 2
done

echo "[SUCCESS] VOICEVOX 起動完了！"
echo "[SYSTEM] エッジアプリ(app.py)を起動します..."

# エッジアプリ起動
source /home/pbl8/edge/env/bin/activate
python3 /home/pbl8/edge/app.py